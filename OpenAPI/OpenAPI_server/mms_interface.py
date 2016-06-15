# -*- coding: utf-8 -*-

import json
import base64
import datetime
from common.iot_request_handler import IotRequestHandler
from common.iot_msg import *
from OpenAPI_server.http_utils import http_client_pool
from common.iot_procdef import *
from OpenAPI_server.serv_zmq_cfg import stream_procs
from common.msgtypedef import *
from common.eventno import *
from common.settings import STORAGE_DIR, MEMCACHE_HOST, MMS_HANDLE_TIME, MMS_LOCK_CHECK_INTERVAL
from common.api_tagdef import TAG_APPKEY
from DistributedLock.distributed_lock import *
from datetime import timedelta
from tornado.ioloop import IOLoop
from tornado.web import asynchronous
import memcache

author = "jxh"


# 彩信对外接口
class MmsInterface(IotRequestHandler):
    mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)

    def __init__(self, application, request, **kwargs):
        super(MmsInterface, self).__init__(application, request, **kwargs)
        self.remain_checktimes = MMS_HANDLE_TIME / MMS_LOCK_CHECK_INTERVAL
        # self.mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)
        # appkey = self.request.headers.get(TAG_APPKEY, '')
        # self.lock_name = appkey + "_mms"
        self.lock_name = ""

    def data_received(self, chunk):
        pass

    @asynchronous
    def post(self):
        try:
            self.lock_name = self.request.headers.get(TAG_APPKEY, '') + "_mms"
            result = distributed_lock_require(MmsInterface.mem_handle, self.lock_name, MMS_HANDLE_TIME / 1000)
            if result is True:
                self.handle_sendmms_request()
            else:
                try:
                    timeout_delta = timedelta(microseconds=MMS_LOCK_CHECK_INTERVAL)
                    retry_timer = IOLoop.current().add_timeout(timeout_delta, self.require_lock)
                    if retry_timer is None:
                        logging.info("Add the timeout task failed")
                        self.set_status(501)
                        self.write({"status": 1000, "status_text": "resource busy"})
                        self.finish()
                        return

                except Exception as err_info:
                    logging.info("Add the timeout task failed: %s" % err_info)
                    self.set_status(501)
                    self.write({"status": 1000, "status_text": "parse json fail"})
                    self.finish()
                    return

        except Exception as err_info:
            logging.error("Require the lock failed: %s" % err_info)
            distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "parse json fail"})
            self.finish()
            return

    def require_lock(self):
        result = distributed_lock_require(MmsInterface.mem_handle, self.lock_name, MMS_HANDLE_TIME / 1000)
        if result is True:
            self.handle_sendmms_request()
        elif self.remain_checktimes > 0:
            self.remain_checktimes -= 1
            timeout_delta = timedelta(microseconds=MMS_LOCK_CHECK_INTERVAL)
            retry_timer = IOLoop.current().add_timeout(timeout_delta, self.require_lock)
            if retry_timer is None:
                logging.info("Add the timeout task failed")
                self.set_status(501)
                self.write({"status": 1000, "status_text": "Internal system error"})
                self.finish()
                return
        else:
            logging.info("Get the lock timeout")
            self.write({"status": 1000, "status_text": "resource busy"})
            self.finish()
            return

    def handle_sendmms_request(self):
        """{
        "dest_telno": ["telno1","telno2","telno3" ],
        "title": "彩信标题",
        "pages": [
            {
                "img": {
                    "type": "jpg",
                    "content": "图片内容Base64编码"
                },
                "audio": {
                    "type": "mid",
                    "content": "音频内容Base64编码"
                },
                "video": {
                    "type": "3gp",
                    "content": "视频内容Base64编码"
                },
                "text": "文本"
            }
        ]
        }"""
        # 解析请求内容到json格式
        try:
            req = self.request.body.decode()
            req_dict = json.loads(req)

        except Exception as err_info:
            logging.error("Parse the body failed: %s" % err_info)
            distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "parse json fail"})
            self.finish()
            return

        phone_list = req_dict.get("dest_telno", None)
        if phone_list is None:
            distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
            logging.error("The request: not have pages node" % req)
            self.write({"status": 1000, "status_text": "no phonelist node"})
            self.finish()
            return

        token_keyname = "_max_rate_" + self.lock_name
        remain_token = MmsInterface.mem_handle.get(token_keyname)
        if remain_token is None:
            remain_token = 0

        if remain_token < len(phone_list):
            distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
            logging.error("the bucket token not enough：%s" % token_keyname)
            self.write({"status": 1000, "status_text": "resource busy"})
            self.set_status(501)
            self.finish()
            return

        MmsInterface.mem_handle.set(token_keyname, remain_token - len(phone_list))
        trans_id = self.request.headers.get(TAG_IOT_H_TRANSID, '')
        if trans_id == '':
            try:
                trans_id = "%s%d%s" % (IOT_PROC_MMS, API_SELF_NODE_ID, datetime.datetime.now().strftime("%f"))

            except Exception as err_info:
                logging.info("build trand_id failed: %s" % err_info)
                distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                self.write({"status": 1000, "status_text": "Internal system error"})
                self.finish()
                return

        pages = req_dict.get("pages", None)
        if pages is None:
            distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
            logging.error("The request: not have pages node" % req)
            self.write({"status": 1000, "status_text": "no pages node"})
            self.finish()
            return

        # 存储图片
        iot_dict = req_dict
        index = 0
        for page in pages:
            img_node = page.get("img", None)
            if img_node is not None:
                ret, out_data = self.storage_multimedia("img", img_node)
                if ret is False:
                    distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                    self.write({"status": 1000, "status_text": out_data})
                    self.finish()
                    return
                # iot_dict["pages"][index]["img"]["uri"] = "//capimg/20160519134626.jpg"
                iot_dict["pages"][index]["img"]["uri"] = out_data
                del iot_dict["pages"][index]["img"]["content"]

            audio_node = page.get("audio", None)
            if audio_node is not None:
                ret, out_data = self.storage_multimedia("audio", audio_node)
                if ret is False:
                    distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                    self.write({"status": 1000, "status_text": out_data})
                    self.finish()
                    return
                iot_dict["pages"][index]["audio"]["uri"] = out_data
                del iot_dict["pages"][index]["audio"]["content"]

            video_node = page.get("video", None)
            if video_node is not None:
                ret, out_data = self.storage_multimedia("video", video_node)
                if ret is False:
                    distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                    self.write({"status": 1000, "status_text": out_data})
                    self.finish()
                    return
                iot_dict["pages"][index]["video"]["uri"] = out_data
                del iot_dict["pages"][index]["video"]["content"]
            index += 1

        try:
            ret, msg = self.pack_send_mms_req(self._linkid, iot_dict, trans_id)
            if ret is True:
                # 缓存当前http client
                http_client_pool[self._linkid] = self

                # 发送消息给处理机
                if IOT_PROC_MMS in stream_procs.keys():
                    stream_procs[IOT_PROC_MMS].send(msg)
                    distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                    # Modified by Ennis at 2016-06-12 15:36 for get response from iot
                    logging.info('send msg to iot succ linkid=%d', self._linkid)
                    # self.write({"status": 0, "status_text": "Success"})
                    # self.finish()
                else:
                    logging.error("Can't find process = %s", IOT_PROC_MMS)
                    distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                    self.write({"status": 1000, "status_text": "Internal system error"})
                    self.finish()
            else:
                distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
                self.write({"status": 1000, "status_text": msg, "msg_id": trans_id})
                self.finish()
                logging.error('pack_get_reader_tag_list_req fail! linkid = %d, req = %s', self._linkid, req)

        except Exception as err_info:
            logging.error("Send to iot failed %s" % err_info)
            distributed_lock_release(MmsInterface.mem_handle, self.lock_name)
            self.write({"status": 1000, "status_text": "Internal error"})
            self.finish()
            return

    # Added by Ennis at 2016-06-12 15:36 for get response from iot
    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass

    def pack_send_mms_req(self, linkid, req_body, trans_id):
        """
        生成发送彩信的iot msg
        :param self:
        :param linkid:
        :param req_body:
        :param trans_id:
        :return:
        """
        try:
            msg = pack_full_msg(linkid, MSGTYPE_SEND_MMS, json.dumps(req_body), IOT_PROC_MMS, IOT_EVENT_MMS, "",
                                "", trans_id)
            return True, msg
        except Exception as err:
            self.set_status(501)
            logging.error('pack_send_mms_req fail! err = %s', err)
            return False, "Internal system error"

    def storage_multimedia(self, media_type, media_node):
        """
        :param media_type:
        :param media_node:
        :return:
        """

        file_type = media_node.get("type", None)
        if file_type is None:
            return False, "file type not provided"

        base64_content = media_node.get("content", None)
        if base64_content is None:
            return False, "media content not provided"

        try:
            content = base64.b64decode(base64_content)

        except Exception as err_info:
            logging.info("base64 decode failed: %s" % err_info)
            return False, "content is wrong"

        appkey = self.request.headers.get(TAG_APPKEY, '')
        now = datetime.datetime.now()
        file_name = "caller_%s_%s.%s" % (appkey, now.strftime("%M%S%f"), file_type)
        try:
            with open("%s/%s/%s" % (STORAGE_DIR, "img", file_name), "wb") as file:
                file.write(content)

        except Exception as err_info:
            logging.info("Storage the media failed: %s" % err_info)
            return False, "Internal system error"

        return True, "//%s/%s" % ("img", file_name)
