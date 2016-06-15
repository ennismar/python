# -*- coding: utf-8 -*-
__author__ = 'neo'

from common.mongo_utils import *
from common.api_tagdef import *
from common.iot_msg import *
from common.iot_request_handler import IotRequestHandler


# 终端型号查询
class QueryTermModels(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        try:
            condition = {
                TAG_TYPE: self.get_argument(TAG_TYPE, default=''),
                TAG_COMPANY_CODE: self.get_argument(TAG_COMPANY_CODE, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
            }
            resp = query_term_models(self, condition)
            logging.info('query_term_models, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_term_models fail! err = %s', err)


# 终端型号详细信息查询
class QueryTermModelInfoReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, term_code):
        try:
            resp = query_term_model_detail(self, term_code)
            logging.info('query_term_model_detail, term_code = %s, result = %s', term_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_term_model_detail fail! err = %s', err)


def query_term_models(httpinstance, condition):
    """
    终端型号列表查询
    :param httpinstance:
    :param condition:
    """
    resp = {
        Q_LIMIT: int(condition[Q_LIMIT]),
        Q_OFFSET: int(condition[Q_OFFSET]),
        Q_TOTAL: 0
    }

    qc = {}
    if condition[TAG_COMPANY_CODE] != '':
        qc[TAG_COMPANY_CODE] = condition[TAG_COMPANY_CODE]

    if condition[TAG_TYPE] != '':
        qc[TAG_TYPE] = condition[TAG_TYPE]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['term_model_info'].find(qc, {TAG_NAME: 1, TAG_TERM_CODE: 1, TAG_TYPE: 1, TAG_DESC: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find term_model, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['term_model_info'].find(qc, {TAG_NAME: 1, TAG_TERM_CODE: 1, TAG_TYPE: 1, TAG_DESC: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            term_model_list = []
            for one_model in results.__iter__():
                if "_id" in one_model.keys():
                    del one_model["_id"]

                one_model['herf'] = '/term_models/' + one_model[TAG_TERM_CODE]
                term_model_list.append(one_model)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_MODELS: term_model_list
            }
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('query_c = %s, Exception = %s', condition, err)

    return resp


def query_term_model_detail(httpinstance, term_code):
    """
    查询终端型号详细信息
    :param httpinstance:
    :param term_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['term_model_info'].find_one({TAG_TERM_CODE: term_code}, {"_id": 0, TAG_SERVER_INFO: 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered terminal model"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_term_model_detail fail!, company_code = %s, e = %s', term_code, err)

    return resp
