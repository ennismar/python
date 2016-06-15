# -*- coding: utf-8 -*-
__author__ = 'neo'

import json
import tornado.web

from common.mongo_utils import *
from common.api_tagdef import *
from common.iot_msg import *
from OpenAPI_server.http_utils import http_client_pool, http_client_post
from common.eventno import *
from common.iot_procdef import *
from OpenAPI_server.serv_zmq_cfg import stream_procs
from common.msgtypedef import *
from common.settings import PORTAL_API_URL
from common.auth_utils import resource_auth
from common.resouce_type import RESOURCE_CAMERA
from common.iot_request_handler import IotRequestHandler

# 门户api接口reader操作url
PORTAL_API_CAMERA_URL = PORTAL_API_URL + 'camera'


# 摄像头查询
class CamerasUtils(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    @tornado.web.asynchronous
    def get(self):
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_CAMERA, None,
                                self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                TAG_CAMERA_NAME: self.get_argument(TAG_CAMERA_NAME, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey,
            }
            resp = query_cameras(self, condition)
            logging.info('query_cameras, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_cameras fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self):
        """
        新增一个camera信息
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            camera_info = json.loads(req_body)

            # 增加appkey到请求报文
            camera_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 校验camera_info合法性
            ret, err = camera_info_check(self, camera_info)
            if ret is not True:
                self.write({"status": 1000, "status_text": err})
                self.finish()
                logging.error('reader_info_check fail! err = %s', err)
            else:
                # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
                http_client_post(camera_info, "add", self, PORTAL_API_CAMERA_URL)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('Prog TAG fail! err = %s', err)

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            self.set_status(501)
            pass


# 摄像头详细信息查询
class CameraInfoReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, camera_code):
        try:
            # 资源访问权限校验
            ret = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_CAMERA, camera_code,
                                self.get_argument(TAG_APPID, default=''))
            if ret is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_camera_detail(self, camera_code)
            logging.info('query_camera_detail, camera_code = %s, result = %s', camera_code, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            logging.error('query_camera_detail fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self, camera_code):
        """
        修改单个camera信息
        :param camera_code:
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            camera_info = json.loads(req_body)

            # 增加appkey到请求报文
            camera_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 报文增加camera_code
            camera_info[TAG_CAMERA_CODE] = camera_code

            # 校验camera_code合法性
            ret, err = check_camera_code(self, camera_info[TAG_CAMERA_CODE])
            if ret is not True:
                self.write({"status": 1000, "status_text": err})
                self.finish()
                logging.error('reader_info_check fail! err = %s', err)
            else:
                # 校验camera_info合法性
                ret, err = camera_info_check(self, camera_info)
                if ret is not True:
                    self.write({"status": 1000, "status_text": err})
                    self.finish()
                    logging.error('reader_info_check fail! err = %s', err)
                else:
                    # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
                    http_client_post(camera_info, "edit", self, PORTAL_API_CAMERA_URL)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('Prog TAG fail! err = %s', err)

    @tornado.web.asynchronous
    def delete(self, camera_code):
        """
        删除一个camera信息
        :param camera_code:
        """
        try:
            # 获取request 内容
            camera_info = {'camera_code': camera_code, TAG_APPKEY: self.request.headers.get(TAG_APPKEY)}

            # 增加appkey到请求报文

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(camera_info, "delete", self, PORTAL_API_CAMERA_URL)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('Prog TAG fail! err = %s', err)

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            self.set_status(501)
            pass


# 摄像头抓拍
class CameraCaptureReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    @tornado.web.asynchronous
    def get(self, camera_code):
        try:
            # 资源访问权限校验
            ret = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_CAMERA, camera_code,
                                self.get_argument(TAG_APPID, default=''))
            if ret is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            ret, msg = pack_camera_take_picture(self, self._linkid, camera_code, self.request.headers.get(TAG_IOT_H_TRANSID, ''))
            if ret is True:
                # 缓存当前http client
                http_client_pool[self._linkid] = self

                # 发送消息给处理机
                if IOT_PROC_CAMERA_CTRL in stream_procs.keys():
                    stream_procs[IOT_PROC_CAMERA_CTRL].send(msg)
                    logging.debug('Send Camera Capture Req Succ! linkid = %d, camera_code = %s', self._linkid, camera_code)
                else:
                    logging.error("Can't find process = %s", IOT_PROC_CAMERA_CTRL)
                    self.write({"status": 1000, "status_text": "Internal system error"})
                    self.finish()
            else:
                self.write({"status": 1000, "status_text": msg})
                self.finish()
                logging.error('pack_get_camera_tag_list_req fail! linkid = %d, camera_code = %s', self._linkid, camera_code)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('CameraCaptureReq fail! err = %s', err)

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


def get_term_code_by_camera_code(handler, db_name, collection, camera_code):
    """
    根据reader_code获取对应的term_code
    :param handler:
    :param db_name:
    :param collection:
    :param camera_code:
    :return:
    """
    try:
        return True, mongo_cli[db_name][collection].find_one({TAG_CAMERA_CODE: camera_code})[TAG_TERM_CODE]
    except Exception as err:
        handler.set_status(501)
        logging.error("Can't find term_code by camera_code! db = %s.%s, camera_code = %s, err = %s", db_name, collection, camera_code, err)
        return False, "unregistered camera"


def pack_camera_take_picture(handler, linkid, camera_code, trans_id):
    """
    生成获取taglist的消息
    :param handler:
    :param linkid:
    :param camera_code:
    :param trans_id:
    :return:
    """
    try:
        # 获取term_code
        ret, term_code = get_term_code_by_camera_code(handler, DB_IOT, 'camera_info', camera_code)
        logging.debug('camera_code = %s, term_code = %s', camera_code, term_code)
        if ret is False:
            return False, "unregistered camera"

        req_dict = {TAG_CAMERA_CODE: camera_code}
        msg = pack_full_msg(linkid, MSGTYPE_CAMERA_REQ_CAPTURE, json.dumps(req_dict),
                            IOT_PROC_CAMERA_CTRL, IOT_TCPINTF_TO_PF_REQ, term_code, camera_code, trans_id)
        return True, msg
    except Exception as err:
        handler.set_status(501)
        logging.error('pack_get_camera_tag_list_req fail! err = %s', err)
        return False, "Internal system error"


def query_cameras(handler, condition):
    """
    摄像头列表查询
    :param handler:
    :param condition:
    """
    resp = ''

    qc = {}
    if condition[TAG_CAMERA_NAME] != '':
        qc[TAG_CAMERA_NAME] = condition[TAG_CAMERA_NAME]

    qc[TAG_APPKEY] = condition[TAG_APPKEY]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['camera_info'].find(qc, {TAG_CAMERA_NAME: 1, TAG_CAMERA_CODE: 1}).count()
    except Exception as err:
        handler.set_status(501)
        logging.info("Can't find reader_info, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['camera_info'].find(qc, {TAG_CAMERA_NAME: 1, TAG_CAMERA_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            camera_list = []
            for one_camera in results.__iter__():
                if "_id" in one_camera.keys():
                    del one_camera["_id"]

                one_camera['herf'] = '/cameras/' + one_camera[TAG_CAMERA_CODE]
                camera_list.append(one_camera)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_CAMERAS: camera_list
            }
        except Exception as err:
            handler.set_status(501)
            logging.error('query_c = %s, Exception = %s', condition, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: count
        }

    return resp


def query_camera_detail(handler, camera_code):
    """
    查询摄像头详细信息
    :param handler:
    :param camera_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['camera_info'].find_one({TAG_CAMERA_CODE: camera_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered camera"}
        else:
            resp = info
    except Exception as err:
        handler.set_status(501)
        logging.error('query_camera_detail fail!, reader_code = %s, e = %s', camera_code, err)

    return resp


def camera_info_check(handler, camera_info):
    """
    camera信息合法性校验
    :param handler:
    :param camera_info:
    """
    # 校验状态
    if TAG_STATUS in camera_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['dictionary'].find({TAG_DICT_VALUE: str(camera_info[TAG_STATUS]), TAG_DICT_TYPE: TAG_STATUS}).count()
            if ret == 0:
                return False, "status is invalid"
        except Exception as err:
            handler.set_status(501)
            logging.error('check status fail!, status = %s, e = %s', camera_info[TAG_STATUS], err)
            return False, "Internal System Error"
    else:
        return False, TAG_STATUS + " is None"

    # 校验读写器厂商
    if TAG_COMPANY_CODE in camera_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['company_info'].find({TAG_COMPANY_CODE: camera_info[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "unsupported company"
        except Exception as err:
            handler.set_status(501)
            logging.error('check company fail!, company_code = %s, e = %s', camera_info['company_code'], err)
            return False, "Internal System Error"
    else:
        return False, TAG_COMPANY_CODE + " is None"

    # 校验读写器型号
    if TAG_TERM_CODE in camera_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['term_model_info'].find({TAG_TERM_CODE: camera_info[TAG_TERM_CODE], TAG_COMPANY_CODE: camera_info[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "term_code is invalid"
        except Exception as err:
            handler.set_status(501)
            logging.error('check term_code fail!, term_code = %s, e = %s', camera_info[TAG_TERM_CODE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_TERM_CODE + " is None"

    return True, ""


# 校验reader_code
def check_camera_code(handler, camera_code):
    try:
        ret = mongo_cli[DB_IOT]['camera_info'].find({TAG_CAMERA_CODE: camera_code}).count()
        if ret == 0:
            return False, "camera_code is invalid"
        else:
            return True, ""
    except Exception as err:
        handler.set_status(500)
        logging.error('check_reader_code fail!, camera_code = %s, e = %s', camera_code, err)
        return False, "Internal System Error"
