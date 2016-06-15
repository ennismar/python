# -*- coding: utf-8 -*-
__author__ = 'neo'


import time
import datetime
from common.api_tagdef import *
from common.mongo_utils import *
from common.auth_utils import resource_auth
from common.resouce_type import RESOURCE_IDCARD
from common.iot_request_handler import IotRequestHandler


# 一卡通平台pos列表信息查询
class SmIdCardList(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的用户信息卡列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_IDCARD, None,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                TAG_IDCARD_NO: self.get_argument(TAG_NAME, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey,
            }
            resp = query_sm_idcard(self, condition)
            logging.info('query_sm_idcard, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_idcard fail! err = %s', err)


# 一卡通平台pos详细信息查询
class SmIdCardInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, idcard_code):
        """
        获取单个用户信息卡详细信息
        :param idcard_code: 设备卡号
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_IDCARD, idcard_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_sm_idcard_detail(self, idcard_code)
            logging.info('query_sm_idcard_detail, idcard_no = %s, result = %s', idcard_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_idcard fail! err = %s', err)


class QueryIdcardPosTransInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, idcard_code, start_time, end_time, sort_flag):
        """
        查询用户的pos消费记录
        :param idcard_code: 用户标识
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param sort_flag: asc/desc
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_IDCARD, idcard_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_IDCARD_CODE: idcard_code,
                TAG_START_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(start_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_END_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(end_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_SORT_FLAG: sort_flag,
            }
            resp = query_sm_idcard_pos_transactions(condition)
            self.write(resp)
            self.finish()
            logging.info('query_sm_idcard_pos_transactions, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_idcard_pos_transactions fail! err = %s', err)


def query_sm_idcard_pos_transactions(condition):
    """
    用户消费记录查询
    :param condition:
    """
    resp = ''

    # 根据idcode_code查找对应的asn
    qc = {
        TAG_IDCARD_CODE: condition[TAG_IDCARD_CODE]
    }

    try:
        asn = mongo_cli[DB_IOT]['idcard'].find_one(qc)
    except Exception as err:
        logging.error('get idcard info fail!, qc = %s, err = %s', qc, err)
        raise err

    if asn.get('currentAsn', '') == '':
        logging.error("unregistered idcard! idcard_code = %s", condition[TAG_IDCARD_CODE])
        return {"status": 1000, "status_text": "unregistered idcard"}

    # 查询term op表
    qc = {
        'req.cardAsn': asn['currentAsn'],
        TAG_TERM_OP_REQTYPE: 'smartcard_pos_trans',
        TAG_TERM_OP_OPTIME: {'$gte': condition[TAG_START_TIME], '$lte': condition[TAG_END_TIME]},
    }

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['term_op'].find(qc, {TAG_TERM_OP_REQ: 1, "_id": 0}).count()
    except Exception as err:
        logging.info("Can't find idcard_pos_transactions_info, qc = %s, err = %s", qc, err)
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
            logging.error('idcard_pos_transactions_info Exception! query_c = %s, Exception = %s', qc, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: 0
        }

    return resp


class QueryIdcardAccessControllerTransInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, idcard_code, start_time, end_time, sort_flag):
        """
        查询用户的门禁刷卡记录
        :param idcard_code: 用户标识
        :param start_time: 开始时间
        :param end_time: 结束时间
        :param sort_flag: asc/desc
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_IDCARD, idcard_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_IDCARD_CODE: idcard_code,
                TAG_START_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(start_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_END_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(end_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_SORT_FLAG: sort_flag,
            }
            resp = query_sm_idcard_access_transactions(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_sm_idcard_access_transactions, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_idcard_access_transactions fail! err = %s', err)


def query_sm_idcard_access_transactions(httpinstance, condition):
    """
    用户门禁刷卡记录查询
    :param httpinstance:
    :param condition:
    """
    resp = ''

    # 根据idcode_code查找对应的asn
    qc = {
        TAG_IDCARD_CODE: condition[TAG_IDCARD_CODE]
    }

    try:
        asn = mongo_cli[DB_IOT]['idcard'].find_one(qc)
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('get idcard info fail!, qc = %s, err = %s', qc, err)
        raise err

    if asn.get('currentAsn', '') == '':
        logging.error("unregistered idcard! idcard_code = %s", condition[TAG_IDCARD_CODE])
        return {"status": 1000, "status_text": "unregistered idcard"}

    # 查询term op表
    qc = {
        'req.asn': asn['currentAsn'],
        TAG_TERM_OP_REQTYPE: 'smartcard_access_trans',
        TAG_TERM_OP_OPTIME: {'$gte': condition[TAG_START_TIME], '$lte': condition[TAG_END_TIME]},
    }

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['term_op'].find(qc, {TAG_TERM_OP_REQ: 1, "_id": 0}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find idcard_access_transactions_info, qc = %s, err = %s", qc, err)
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
            logging.error('idcard_access_transactions_info Exception! query_c = %s, Exception = %s', qc, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: 0
        }

    return resp


def query_sm_idcard(httpinstance, condition):
    """
    用户信息卡列表查询
    :param httpinstance:
    :param condition:
    """
    resp = ''

    qc = {}
    if condition[TAG_IDCARD_NO] != '':
        qc[TAG_IDCARD_NO] = condition[TAG_IDCARD_NO]

    if condition[TAG_APPKEY] != '':
        qc[TAG_APPKEY] = condition[TAG_APPKEY]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['idcard'].find(qc, {TAG_IDCARD_CODE: 1, TAG_IDCARD_NO: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find idcard, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['idcard'].find(qc, {TAG_IDCARD_CODE: 1, TAG_IDCARD_NO: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            idcard_list = []
            for one_idcard in results.__iter__():
                if "_id" in one_idcard.keys():
                    del one_idcard["_id"]

                one_idcard['herf'] = '/idcard/' + one_idcard[TAG_IDCARD_CODE]
                idcard_list.append(one_idcard)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_IDCARD: idcard_list
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


def query_sm_idcard_detail(httpinstance, idcard_code):
    """
    查询用户信息卡详细信息
    :param httpinstance:
    :param idcard_code: 卡编码
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['idcard'].find_one({TAG_IDCARD_CODE: idcard_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered idcard"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_sm_idcard_detail fail!, idcard_code = %s, e = %s', idcard_code, err)

    return resp
