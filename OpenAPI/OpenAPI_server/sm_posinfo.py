# -*- coding: utf-8 -*-
__author__ = 'neo'


import time
import datetime
from common.api_tagdef import *
from common.mongo_utils import *
from common.auth_utils import resource_auth
from common.resouce_type import RESOURCE_POS
from common.iot_request_handler import IotRequestHandler

# 一卡通平台pos列表信息查询
class SmPosList(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的pos列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_POS, None, self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                TAG_NAME: self.get_argument(TAG_NAME, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey
            }
            resp = query_sm_pos(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_sm_pos, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_pos fail! err = %s', err)


# 一卡通平台pos详细信息查询
class SmPosInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, pos_code):
        """
        获取单个pos详细信息
        :param pos_code: Pos终端编号
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_POS, pos_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_sm_pos_detail(self, pos_code)
            logging.info('query_reader_detail, pos_code = %s, result = %s', pos_code, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_reader_detail fail! err = %s', err)


class QueryPosTransInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, pos_code, start_time, end_time, sort_flag):
        """
        查询指定pos的交易记录
        :param pos_code: 查询的pos编码
        :param start_time: 查询开始时间
        :param end_time: 查询结束时间
        :param sort_flag: 排序表示，asc/desc
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_POS, pos_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_POS_CODE: pos_code,
                TAG_START_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(start_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_END_TIME: datetime.datetime.fromtimestamp(time.mktime(time.gmtime(time.mktime(time.strptime(end_time,"%Y-%m-%d %H:%M:%S"))))),
                TAG_SORT_FLAG: sort_flag,
            }
            resp = query_sm_pos_transactions(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_sm_pos, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_pos fail! err = %s', err)


def query_sm_pos_transactions(httpinstance, condition):
    """
    pos机刷卡记录查询
    :param httpinstance:
    :param condition:
    """
    resp = ''

    qc = {
        TAG_TERM_OP_DEVICE_CODE: condition[TAG_POS_CODE],
        TAG_TERM_OP_REQTYPE: 'smartcard_pos_trans',
        TAG_TERM_OP_OPTIME: {'$gte': condition[TAG_START_TIME], '$lte': condition[TAG_END_TIME]},
    }

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['term_op'].find(qc, {TAG_TERM_OP_REQ: 1, "_id": 0}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find pos_transactions_info, qc = %s, err = %s", qc, err)
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
                # 如果没有req字段，则总数减一，不返回这条数据
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
            logging.error('pos_transactions_info Exception! query_c = %s, Exception = %s', qc, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: 0
        }

    return resp


def query_sm_pos(httpinstance, condition):
    """
    POS列表查询
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
        count = mongo_cli[DB_IOT]['pos_info'].find(qc, {TAG_POS_CODE: 1, TAG_NAME: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find pos_info, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['pos_info'].find(qc, {TAG_NAME: 1, TAG_POS_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            pos_list = []
            for one_pos in results.__iter__():
                if "_id" in one_pos.keys():
                    del one_pos["_id"]

                one_pos['herf'] = '/pos/' + one_pos[TAG_POS_CODE]
                pos_list.append(one_pos)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_POS: pos_list
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


def query_sm_pos_detail(httpinstance, pos_code):
    """
    查询POS详细信息
    :param httpinstance:
    :param pos_code: Pos编码
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['pos_info'].find_one({TAG_POS_CODE: pos_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered pos"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_sm_pos_detail fail!, pos_code = %s, e = %s', pos_code, err)

    return resp
