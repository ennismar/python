# -*- coding: utf-8 -*-
__author__ = 'neo'

import datetime
import urllib.parse

import memcache

from OpenAPI_server.http_utils import *
from common.iot_request_handler import IotRequestHandler
from common.mongo_utils import *
from common.settings import MEMCACHE_HOST
from common.auth_utils import resource_auth
from common.api_tagdef import *
from common.resouce_type import RESOURCE_SMS
from DistributedLock.distributed_lock import distributed_lock_require, distributed_lock_release

if IS_DEBUG is 1:
    URL_ADDR = 'http://192.168.1.201:5011/sendSMSCode'
else:
    URL_ADDR = 'http://121.43.225.10/sendSMSCode?account=%s&password=%s&phone=%s&content=%s&template=%s'
smsRespDataDict = {0: "success",
                   -1: "param error",
                   -2: "phonenum error",
                   -3: "send too fast",
                   -4: "service close",
                   -5: "content to long",
                   -6: "template number error",
                   -7: "content not match template number",
                   -8: "setting error",
                   -9: "phonenum error",
                   -10: "blacklist phonenum",
                   -11: "lack of balance",
                   -12: "have sensitive word",
                   -13: "submit time error",
                   -14: "ip error",
                   -15: "password error",
                   -16: "account error"}


class SmsStatusQuery(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, trans_id):
        """
        根据sms_id，查询短信发送状态
        :param trans_id: 发送短信响应报文里的msg_id
        """
        try:
            info = mongo_cli[DB_IOT]['sms_log'].find_one({TAG_IOT_H_TRANSID: trans_id}, {"_id": 0})
            if info is None:
                self.write({"status": 1000, "status_text": "msg_id is not found!"})
            else:
                logging.info('mms = %s', info)
                sndtime = info.get("date")
                info["date"] = str(sndtime)
                self.write(info)
            self.finish()
        except Exception as err:
            logging.error('Find mms fail! err = %s', err)
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()


class SmsSend(IotRequestHandler):
    mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)

    def data_received(self, chunk):
        pass

    @tornado.web.asynchronous
    def post(self):
        """
        发送短信，http body为json格式，彩信内容，utf8格式
        {
            "dest_telno": "telephone",
            "content":"短信内容"
        }
        """
        try:
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_SMS, None,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            logging.info("Receive send sms require")
            req = self.request.body.decode("utf-8")
            self.result = log_send_sms(self, req)
            if self.result is None:
                logging.info("Log the sms failed %s" % req)

            url, err = pack_sms_url(self, req)
            if url is not None and url != "":
                # 流量控制检测
                if check_app_auth(self.request.headers.get(TAG_APPKEY, '')):
                    logging.info("Will post url:" + url)
                    future_data = http_client_post_with_result(None, 'POST', self, url)
                    future_data.add_done_callback(self.get_result)
                else:
                    self.write({"status": 1000, "status_text": "frequency exceeds the limit"})
                    self.finish()
            else:
                self.write({"status": 1000, "status_text": err})
                self.finish()

        except Exception as err:
            logging.error('Send sms fail! err = %s', err)
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()

    @tornado.web.asynchronous
    def get_result(self, future_data):
        try:
            logging.info("have get the result")
            resp_data = future_data.result()
            logging.info(resp_data)
            resp_code = int(resp_data.body)
            if resp_code >= 0:
                resp_desp = smsRespDataDict.get(0, "")
            else:
                resp_desp = smsRespDataDict.get(resp_code, "")

            if resp_desp is None or resp_desp == "":
                snd_resp = {"status_code": 1000, "status_text": "response code  not recognized"}
            elif resp_code < 0:
                snd_resp = {"status_code": 1000, "status_text": resp_desp}
            else:
                snd_resp = {"msg_id": str(resp_code)}
                update_sms_log(self, self.result, resp_code)

            self.write(snd_resp)
            self.finish()
        except Exception as e:
            logging.error('Send sms fail! err = %s',  e)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()


def pack_sms_url(httpinstance, reqbody):
    """
    生成发送短信的url地址
    :param httpinstance:
    :param reqbody:请求数据
    :return:
    """
    try:
        try:
            account = SmsSend.mem_handle.get("sms_account")
        except Exception as err:
            logging.error("Get the sms_account failed %s " % err)
            return None, "Internal system error"

        try:
            sms_passwd = SmsSend.mem_handle.get("sms_passwd")
        except Exception as err:
            logging.error("Get the sms_passwd failed %s " % err)
            return None, "Internal system error"

        logging.info('account:%s , passwd %s', account, sms_passwd)
        bodydict = json.loads(reqbody)

        telephone = bodydict.get("dest_telno", "")
        content = bodydict.get("content", "")
        # 如果没有template字段，就是用系统默认的短信模板进行发送
        template = bodydict.get("template", '1033')
        logging.info("content %s  template : %s", content, template)
        if not isinstance(telephone, str):
            return None, "telephone type error"
        if telephone == "" or content == "":
            return None, "not have telephone or content"
        content = urllib.parse.quote(content.encode("utf-8"))

        url = URL_ADDR % (account, sms_passwd, telephone, content, template)
        return url, ""

    except Exception as err:
        httpinstance.set_status(500)
        logging.error('pack_sms_url fail! err = %s', err)
        return None, "Internal system error"


def log_send_sms(httpinstance, reqbody):
    """
    :param httpinstance:
    :param reqbody:
    """
    try:
        logging.info("Will log the send log")
        bodydict = json.loads(reqbody)
        post = {"data": bodydict,
                "date": datetime.datetime.utcnow()}
        result = mongo_cli[DB_IOT]["sms_log"].insert(post)
        return result

    except Exception as err:
        httpinstance.set_status(500)
        logging.error('log_send_sms fail! err = %s', err)


def update_sms_log(httpinstance, object_id, msg_id):
    if object_id is None or msg_id is None:
        logging.info("update sms log parameter wrong")
        return

    try:
        update_data = {"$set": {TAG_IOT_H_TRANSID: str(msg_id)}}
        mongo_cli[DB_IOT]["sms_log"].update({"_id": object_id}, update_data)

    except Exception as err_info:
        httpinstance.set_status(500)
        logging.error('log_send_sms fail! err = %s', err_info)


def check_app_auth(app_key):
    """
    sms流量控制校验，每次发送消耗一个令牌
    :param app_key:
    :return:
    """
    if not app_key:
        return False

    # 获取分布式锁
    lock_name = app_key + '_sms'
    if not distributed_lock_require(SmsSend.mem_handle, lock_name, 3):
        logging.error('get app[%s] distributed lock fail', app_key)
        return False

    mc_key = '_max_rate_{}_{}'.format(app_key, 'sms')

    # 获取剩余令牌数
    try:
        token = int(SmsSend.mem_handle.get(mc_key))
    except Exception as err:
        logging.error('get app[%s] token fail, err: ', app_key, err)
        # 释放分布式锁
        distributed_lock_release(SmsSend.mem_handle, lock_name)
        return False

    # 令牌不足
    if token < 1:
        logging.error('app[%s] token[%d] not enough', app_key, token)
        # 释放分布式锁
        distributed_lock_release(SmsSend.mem_handle, lock_name)
        return False

    # 更新令牌数
    token -= 1
    try:
        SmsSend.mem_handle.set(mc_key, token)
    except Exception as err:
        logging.error('set app[%s] token to [%d] fail, err: ', app_key, token, err)
        # 释放分布式锁
        distributed_lock_release(SmsSend.mem_handle, lock_name)
        return False

    # 释放分布式锁
    distributed_lock_release(SmsSend.mem_handle, lock_name)

    logging.info('set app[%s] token to [%d]', app_key, token)
    return True
