# -*- coding: utf-8 -*-
__author__ = 'neo'

from common.mongo_utils import *
from common.api_tagdef import *
from common.iot_msg import *
from common.iot_request_handler import IotRequestHandler


# 网关列表查询
class QueryGateways(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        try:
            condition = {
                TAG_GATEWAY_NAME: self.get_argument(TAG_GATEWAY_NAME, default=''),
                TAG_GATEWAY_TYPE: self.get_argument(TAG_GATEWAY_TYPE, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
            }
            resp = query_gateways(self, condition)
            logging.info('query_gateways, condition = %s, result = %s', condition, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            logging.error('query_gateways fail! err = %s', err)


# 网关详细信息查询
class QueryGatewayInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, gate_code):
        try:
            resp = query_gateway_detail(self, gate_code)
            logging.info('query_gateway_detail, gate_code = %s, result = %s', gate_code, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            logging.error('query_gateway_detail fail! err = %s', err)


def query_gateways(handler, query_condition):
    """
    查询网关列表
    :param handler:
    :param query_condition:
    """
    resp = {
        Q_LIMIT: int(query_condition[Q_LIMIT]),
        Q_OFFSET: int(query_condition[Q_OFFSET]),
        Q_TOTAL: 0
    }

    qc = {}
    if query_condition[TAG_GATEWAY_NAME] != '':
        qc[TAG_GATEWAY_NAME] = query_condition[TAG_GATEWAY_NAME]

    if query_condition[TAG_GATEWAY_TYPE] != '':
        qc[TAG_GATEWAY_TYPE] = query_condition[TAG_GATEWAY_TYPE]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['gateway_info'].find(qc, {TAG_GATEWAY_NAME: 1, TAG_GATEWAY_CODE: 1}).count()
    except Exception as err:
        handler.set_status(501)
        logging.info("Can't find gateway, condition = %s, err = %s", query_condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['gateway_info'].find(qc, {TAG_GATEWAY_NAME: 1, TAG_GATEWAY_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(query_condition[Q_OFFSET])).limit(int(query_condition[Q_LIMIT]))

            gateway_list = []
            for one_gateway in results.__iter__():
                if "_id" in one_gateway.keys():
                    del one_gateway["_id"]

                one_gateway['herf'] = '/gateways/' + one_gateway[TAG_GATEWAY_CODE]
                gateway_list.append(one_gateway)

            resp = {
                Q_LIMIT: int(query_condition[Q_LIMIT]),
                Q_OFFSET: int(query_condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_GATEWAYS: gateway_list
            }
        except Exception as err:
            handler.set_status(501)
            logging.error('query_c = %s, Exception = %s', query_condition, err)

    return resp


def query_gateway_detail(handler, gate_code):
    """
    查询网关详细信息
    :param handler:
    :param gate_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['gateway_info'].find_one({TAG_GATEWAY_CODE: gate_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered gateway"}
        else:
            resp = info
    except Exception as err:
        handler.set_status(501)
        logging.error('query_gateway_detail fail!, gate_code = %s, e = %s', gate_code, err)

    return resp
