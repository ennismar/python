# -*- coding: utf-8 -*-
__author__ = 'neo'


import json
from common.mongo_utils import *
from common.iot_request_handler import IotRequestHandler
from common.iot_msg import *
from OpenAPI_server.http_utils import http_client_pool
from common.iot_procdef import *
from OpenAPI_server.serv_zmq_cfg import stream_procs
from common.msgtypedef import *
from common.eventno import *


class MmsStatusQuery(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, msg_id):
        """
        根据mms_id，查询彩信发送状态
        :param trans_id: 发送短信响应报文里的msg_id
        """
        try:
            info = mongo_cli[DB_IOT]['mms_log'].find_one({"msgid": msg_id}, {"_id": 0})
            if info is None:
                self.write({"status": 1000, "status_text": "msg_id is not found!"})
            else:
                logging.info('mms = %s', info)
                info["sndtime"] = str(info["sndtime"])
                self.write(info)
        except Exception as err:
            logging.error('Find mms fail! err = %s', err)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})


class MmsSend(IotRequestHandler):
    def data_received(self, chunk):
        pass


    def post(self):
        """
        发送彩信，http body为json格式，彩信内容，utf8格式
        {
            "dest_telno": ["telno1", "telno2", "telno3"],
            "title": "彩信标题",
            "pages": [
                {
                    "img": {"type":"gif", "uri":"图片文件uri"},
                    "audio": {"type":"mid", "uri":"声音文件uri"},
                    "video": {"type":"3gp", "uri":"视频文件uri"},
                    "text": "文本"
                },
                {
                    "img": {"type":"gif", "uri":"图片文件uri"},
                    "audio": {"type":"mid", "uri":"声音文件uri"},
                    "video": {"type":"3gp", "uri":"视频文件uri"},
                    "text": "文本"
                }
            ]
        }
        """
        try:
            # TODO 验证app是否可以发送彩信
            req = self.request.body.decode()
            trans_id = self.request.headers.get(TAG_IOT_H_TRANSID, '')
            ret, msg = pack_send_mms_req(self, self._linkid, req, trans_id)
            if ret is True:
                # 缓存当前http client
                http_client_pool[self._linkid] = self

                # 发送消息给处理机
                if IOT_PROC_MMS in stream_procs.keys():
                    stream_procs[IOT_PROC_MMS].send(msg)
                    logging.debug('Send Read Taglist Req Succ! linkid = %d, req = %s', self._linkid, req)
                    # Modified by Ennis at 2016-06-12 15:36 for get response from iot
                    # self.write({"status": 0, "status_text": "Success"})
                else:
                    logging.error("Can't find process = %s", IOT_PROC_MMS)
                    self.write({"status": 1000, "status_text": "Internal system error"})
            else:
                self.write({"status": 1000, "status_text": msg, "msg_id": trans_id})
                logging.error('pack_get_reader_tag_list_req fail! linkid = %d, req = %s', self._linkid, req)
        except Exception as err:
            self.set_status(501)
            logging.error('Send Req to %s fail! err = %s', IOT_PROC_MMS, err)
            self.write({"status": 1000, "status_text": "Internal system error"})

    # Added by Ennis at 2016-06-12 15:36 for get response from iot
    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


def pack_send_mms_req(handler, linkid, req_body, trans_id):
    """
    生成发送彩信的iot msg
    :param handler:
    :param linkid:
    :param req_body:
    :param trans_id:
    :return:
    """
    try:
        msg = pack_full_msg(linkid, MSGTYPE_SEND_MMS, json.dumps(req_body), IOT_PROC_MMS, IOT_EVENT_MMS, "", "", trans_id)
        return True, msg
    except Exception as err:
        handler.set_status(501)
        logging.error('pack_send_mms_req fail! err = %s', err)
        return False, "Internal system error"
