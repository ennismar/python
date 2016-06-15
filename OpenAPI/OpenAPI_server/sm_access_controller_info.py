# -*- coding: utf-8 -*-
__author__ = 'neo'


import time
import datetime
from common.api_tagdef import *
from common.mongo_utils import *
from common.auth_utils import resource_auth
from common.resouce_type import RESOURCE_ACCESS_CONTROLLER
from common.iot_request_handler import IotRequestHandler


# 一卡通平台门禁列表信息查询
class SmAccessControllerList(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的门禁控制器列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_ACCESS_CONTROLLER, None,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                TAG_NAME: self.get_argument(TAG_NAME, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey,
            }
            resp = query_sm_access_controller(self, condition)
            logging.info('query_sm_access_controller, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_access_controller fail! err = %s', err)


# 一卡通平台门禁详细信息查询
class SmAccessControllerInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, productnumber):
        """
        获取单个门禁控制器详细信息
        :param productnumber: 设备产品序列号
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_ACCESS_CONTROLLER, productnumber,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_sm_access_controller_detail(self, productnumber)
            logging.info('query_sm_access_controller_detail, productnumber = %s, result = %s', productnumber, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_access_controller_detail fail! err = %s', err)


class QueryAccessControllerTransInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, access_controller_code, start_time, end_time, sort_flag):
        """
        查询指定门禁的交易记录
        :param access_controller_code: 查询的门禁编码
        :param start_time: 查询开始时间
        :param end_time: 查询结束时间
        :param sort_flag: asc/desc
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_ACCESS_CONTROLLER, access_controller_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_ACCESS_CONTROLLER_CODE: access_controller_code,
                TAG_START_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(start_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_END_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(end_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_SORT_FLAG: sort_flag,
            }
            resp = query_sm_access_controller_transactions(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_sm_access_controller, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_access_controller transactions fail! err = %s', err)


def query_sm_access_controller_transactions(httpinstance, condition):
    """
    门禁机刷卡记录查询
    :param httpinstance:
    :param condition:
    """
    resp = ''

    qc = {
        TAG_TERM_OP_DEVICE_CODE: condition[TAG_ACCESS_CONTROLLER_CODE],
        TAG_TERM_OP_REQTYPE: 'smartcard_access_trans',
        TAG_TERM_OP_OPTIME: {'$gte': condition[TAG_START_TIME], '$lte': condition[TAG_END_TIME]},
    }

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['term_op'].find(qc, {TAG_TERM_OP_REQ: 1, "_id": 0}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find access_controller_transactions_info, qc = %s, err = %s", qc, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            if condition[TAG_SORT_FLAG].lower() == 'asc':
                results = mongo_cli[DB_IOT]['term_op'].find(qc, {TAG_TERM_OP_REQ: 1, "_id": 0}).sort(TAG_TERM_OP_OPTIME, SORT_ASC)\
                    .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))
            else:
                results = mongo_cli[DB_IOT]['term_op'].find(qc, {TAG_TERM_OP_REQ: 1, "_id": 0}).sort(TAG_TERM_OP_OPTIME, SORT_DESC)\
                    .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            transactions = []
            for one_trans in results:
                # 避免数据异常，没有req字段，不返回，总数-1
                if TAG_TERM_OP_REQ in one_trans.keys():
                    transactions.append(one_trans[TAG_TERM_OP_REQ])
                else:
                    count -= 1

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_TRANSACTIONS: transactions
            }
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('access_controller_transactions_info Exception! query_c = %s, Exception = %s', qc, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: 0
        }

    return resp


def query_sm_access_controller(httpinstance, condition):
    """
    门禁控制器列表查询
    :param httpinstance:
    :param condition:
    """
    resp = ''

    qc = {}
    if condition[TAG_NAME] != '':
        qc[TAG_NAME] = condition[TAG_NAME]

    if condition[TAG_APPKEY] != '':
        qc[TAG_APPKEY] = condition[TAG_APPKEY]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['access_controller'].find(qc, {TAG_ACCESS_CONTROLLER_CODE: 1, TAG_NAME: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find access_controller, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['access_controller'].find(qc, {TAG_ACCESS_CONTROLLER_CODE: 1, TAG_NAME: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            access_list = []
            for one_access in results.__iter__():
                if "_id" in one_access.keys():
                    del one_access["_id"]

                one_access['herf'] = '/access_controller/' + one_access[TAG_ACCESS_CONTROLLER_CODE]
                access_list.append(one_access)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_ACCESS_CONTROLLER: access_list
            }
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('query_c = %s, Exception = %s', condition, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: 0
        }

    return resp


def query_sm_access_controller_detail(httpinstance, access_controller_code):
    """
    查询门禁控制器详细信息
    :param httpinstance:
    :param access_controller_code: 门禁控制器产品编码
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['access_controller'].find_one({TAG_ACCESS_CONTROLLER_CODE: access_controller_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered access_controller"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_sm_access_controller_detail fail!, access_controller_code = %s, e = %s', access_controller_code, err)

    return resp
