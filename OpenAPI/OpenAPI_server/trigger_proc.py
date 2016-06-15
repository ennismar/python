# -*- coding: utf-8 -*-
__author__ = 'gz'

import json
import tornado.web

from common.mongo_utils import *
from common.api_tagdef import *
from OpenAPI_server.http_utils import http_client_pool, http_client_post
from common.auth_utils import resource_auth
from common.settings import PORTAL_API_URL
from common.resouce_type import RESOURCE_TRIGGER
from common.iot_request_handler import IotRequestHandler


# 门户api接口trigger操作url
PORTAL_API_TRIGGER_URL = PORTAL_API_URL + 'trigger'


# 触发器查询
class TriggersUtils(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的triggers列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_TRIGGER, None,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": u"Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                TAG_TRIGGER_NAME: self.get_argument(TAG_NAME, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey,
            }
            resp = query_triggers(self, condition)
            logging.info('query_triggers, condition = %s, result = %s', condition, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_triggers fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self):
        """
        新增一个trigger信息
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            trigger_info = json.loads(req_body)

            # 增加appkey到请求报文
            trigger_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 校验reader_info合法性
            ret, err = trigger_info_check(self, trigger_info)
            if ret is not True:
                self.write({"status": 1000, "status_text": err})
                self.finish()
                logging.error('trigger_info_check fail! err = %s', err)
            else:
                # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
                http_client_post(trigger_info, "add", self, PORTAL_API_TRIGGER_URL)
        except Exception as err:
            logging.error('add trigger info fail! err = %s', err)
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            self.set_status(500)
            pass


# 触发器详细信息查询
class TriggerInfoReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, trigger_code):
        try:
            # 资源访问权限校验
            ret = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_TRIGGER, trigger_code,
                                self.get_argument(TAG_APPID, default=''))
            if ret is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_trigger_detail(self, trigger_code)
            logging.info('query_trigger_detail, id = %s, result = %s', trigger_code, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_trigger_detail fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self, trigger_code):
        """
        修改单个trigger信息
        :param trigger_code:
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            trigger_info = json.loads(req_body)

            # 增加appkey到请求报文
            trigger_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 报文增加trigger_code
            trigger_info[TAG_TRIGGER_CODE] = trigger_code

            # 校验trigger_code合法性
            ret, err = check_trigger_code(self, trigger_info[TAG_TRIGGER_CODE])
            if ret is not True:
                self.write({"status": 1000, "status_text": err})
                self.finish()
                logging.error('check_trigger_code fail! err = %s', err)
            else:
                # 校验trigger_info合法性
                ret, err = trigger_info_check(self, trigger_info)
                if ret is not True:
                    self.write({"status": 1000, "status_text": err})
                    self.finish()
                    logging.error('trigger_info_check fail! err = %s', err)
                else:
                    # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
                    http_client_post(trigger_info, "edit", self, PORTAL_API_TRIGGER_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('Prog TAG fail! err = %s', err)

    @tornado.web.asynchronous
    def delete(self, trigger_code):
        """
        删除一个trigger信息
        :param trigger_code:
        """
        try:
            # 获取request 内容
            trigger_info = {TAG_TRIGGER_CODE: trigger_code, TAG_APPKEY: self.request.headers.get(TAG_APPKEY)}

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(trigger_info, "delete", self, PORTAL_API_TRIGGER_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('Prog TAG fail! err = %s', err)

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            self.set_status(500)
            pass


def query_triggers(httpinstance, condition):
    """
    触发器列表查询
    :param httpinstance:
    :param condition:
    """
    try:
        resp = ''

        qc = {}
        if condition[TAG_TRIGGER_NAME] != '':
            qc[TAG_TRIGGER_NAME] = condition[TAG_TRIGGER_NAME]

        qc[TAG_APPKEY] = condition[TAG_APPKEY]

        count = 0
        try:
            # 获取总条数
            count = mongo_cli[DB_IOT]['triggers'].find(qc, {TAG_TRIGGER_CODE: 1, TAG_TRIGGER_NAME: 1}).count()
        except Exception as err:
            logging.info("Can't find reader_info, condition = %s, err = %s", condition, err)
            return count, resp

        if count > 0:
            try:
                # 获取数据集
                results = mongo_cli[DB_IOT]['triggers'].find(qc, {TAG_TRIGGER_CODE: 1, TAG_TRIGGER_NAME: 1}).sort("_id", SORT_DESC)\
                    .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

                trigger_list = []
                for one_trigger in results.__iter__():
                    if "_id" in one_trigger.keys():
                        del one_trigger["_id"]

                    one_trigger['herf'] = '/trigger/' + one_trigger[TAG_TRIGGER_CODE]
                    trigger_list.append(one_trigger)

                resp = {
                    Q_LIMIT: int(condition[Q_LIMIT]),
                    Q_OFFSET: int(condition[Q_OFFSET]),
                    Q_TOTAL: count,
                    TAG_TRIGGERS: trigger_list
                }
            except Exception as err:
                logging.error('query_c = %s, Exception = %s', condition, err)
        else:
            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: 0
            }

        return resp
    except Exception:
        httpinstance.set_status(500)
        return {"status": 1000, "status_text": "Internal error"}


def trigger_info_check(httpinstance, trigger_info):
    """
    trigger信息合法性校验
    :param httpinstance:
    :param trigger_info:
    :return:
    """
    # 校验源设备触发消息
    if TAG_TRIGGER_SRC_REQTYPE in trigger_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['dictionary'].find({TAG_DICT_VALUE: trigger_info[TAG_TRIGGER_SRC_REQTYPE], TAG_DICT_TYPE: TAG_MSGTYPE}).count()
            if ret == 0:
                return False, "src req type is invalid"
        except Exception as err:
            logging.error('check msgtype fail!, status = %s, e = %s', trigger_info[TAG_TRIGGER_SRC_REQTYPE], err)
            httpinstance.set_status(500)
            return False, "Internal System Error"
    else:
        return False, TAG_TRIGGER_SRC_REQTYPE + " is None"

    # 校验目的设备触发消息
    if TAG_TRIGGER_DST_REQTYPE in trigger_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['dictionary'].find({TAG_DICT_VALUE: trigger_info[TAG_TRIGGER_DST_REQTYPE], TAG_DICT_TYPE: TAG_MSGTYPE}).count()
            if ret == 0:
                return False, "dst req type is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check msgtype fail!, status = %s, e = %s', trigger_info[TAG_TRIGGER_DST_REQTYPE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_TRIGGER_DST_REQTYPE + " is None"

    # 校验源设备是否存在
    if TAG_TRIGGER_SRC_TYPE in trigger_info.keys() and TAG_TRIGGER_SRC_DEVCODE in trigger_info.keys():
        if trigger_info[TAG_TRIGGER_SRC_DEVCODE].find('reader') >= 0:
            colname = 'reader_info'
            tag_device_code = 'reader_code'
        elif trigger_info[TAG_TRIGGER_SRC_DEVCODE].find('camera') >= 0:
            colname = 'camera_info'
            tag_device_code = 'camera_code'
        else:
            return False, "src device info is invalid"

        if colname != '':
            try:
                ret = mongo_cli[DB_IOT][colname].find({TAG_TERM_CODE: trigger_info[TAG_TRIGGER_SRC_TYPE], tag_device_code: trigger_info[TAG_TRIGGER_SRC_DEVCODE]}).count()
                if ret == 0:
                    return False, "src device not exist"
            except Exception as err:
                httpinstance.set_status(500)
                logging.error('check src device fail!, type/code = %s/%s, e = %s', trigger_info[TAG_TRIGGER_SRC_TYPE], trigger_info[TAG_TRIGGER_SRC_DEVCODE], err)
                return False, "Internal System Error"
    else:
        return False, TAG_TRIGGER_SRC_TYPE + " or " + TAG_TRIGGER_SRC_DEVCODE + " is None"

    # 校验目的设备是否存在
    if trigger_info[TAG_TRIGGER_DST_REQTYPE] != 'mms_send_req':
        if TAG_TRIGGER_DST_TYPE in trigger_info.keys() and TAG_TRIGGER_DST_DEVCODE in trigger_info.keys():
            if trigger_info[TAG_TRIGGER_DST_DEVCODE].find('camera') >= 0:
                colname = 'camera_info'
                tag_device_code = 'camera_code'
            else:
                return False, "dst device info is invalid"

            if colname != '':
                try:
                    ret = mongo_cli[DB_IOT][colname].find({TAG_TERM_CODE: trigger_info[TAG_TRIGGER_DST_TYPE], tag_device_code: trigger_info[TAG_TRIGGER_DST_DEVCODE]}).count()
                    if ret == 0:
                        return False, "dst device not exist"
                except Exception as err:
                    httpinstance.set_status(500)
                    logging.error('check dst device fail!, type/code = %s/%s, e = %s', trigger_info[TAG_TRIGGER_DST_TYPE], trigger_info[TAG_TRIGGER_DST_DEVCODE], err)
                    return False, "Internal System Error"
        else:
            return False, TAG_TRIGGER_DST_TYPE + " or " + TAG_TRIGGER_DST_DEVCODE + " is None"
    else:
        logging.info('dst_type is mms_send_req')

    try:
        ret = mongo_cli[DB_IOT]['triggers'].find(trigger_info).count()
        if ret != 0:
            return False, "trigger exist"
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('check trigger status fail!, status = %s, e = %s', trigger_info, err)
        return False, "Check Trigger Status Fail"

    return True, ""


def query_trigger_detail(httpinstance, trigger_code):
    """
    查询触发器详细信息
    :param httpinstance:
    :param trigger_code:
    :return:
    """
    try:
        info = mongo_cli[DB_IOT]['triggers'].find_one({TAG_TRIGGER_CODE: trigger_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered trigger"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_trigger_detail fail!, id = %s, e = %s', trigger_code, err)
        return {"status": 1000, "status_text": "Internal error"}

    return resp


# 校验trigger_code
def check_trigger_code(httpinstance, trigger_code):
    """

    :param httpinstance:
    :param trigger_code:
    :return:
    """
    try:
        ret = mongo_cli[DB_IOT]['triggers'].find({TAG_TRIGGER_CODE: trigger_code}).count()
        if ret == 0:
            return False, "trigger_code is invalid"
        else:
            return True, ""
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('check_reader_code fail!, trigger_code = %s, e = %s', trigger_code, err)
        return False, "Internal System Error"
