# -*- coding: utf-8 -*-
__author__ = 'neo'

from common.api_tagdef import *
from common.iot_request_handler import IotRequestHandler
from common.mongo_utils import *


# 查询厂商列表
class QueryTermCompanysReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        try:
            condition = {
                TAG_META_DATA: self.get_argument(TAG_META_DATA, default=''),
                TAG_NAME: self.get_argument(TAG_NAME, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
            }
            resp = query_term_companys(self, condition)
            logging.info('query_term_company, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_term_company fail! err = %s', err)


# 查询厂商详细信息
class QueryTermCompanyInfoReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, company_code):
        try:
            resp = query_term_company_detail(self, company_code)
            logging.info('query_term_company_detail, company_code = %s, result = %s', company_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_term_company_detail fail! err = %s', err)


def query_term_companys(httpinstance, query_condition):
    """
    查询厂商列表
    :param httpinstance:
    :param query_condition:
    """
    resp = {
        Q_LIMIT: int(query_condition[Q_LIMIT]),
        Q_OFFSET: int(query_condition[Q_OFFSET]),
        Q_TOTAL: 0
    }

    qc = {}
    meta_list = []
    for one_meta in query_condition[TAG_META_DATA].split(','):
        meta_list.append(one_meta.strip())

    qc[TAG_META_DATA] = {'$all': meta_list}

    if query_condition[TAG_NAME] != '':
        qc[TAG_NAME] = query_condition[TAG_NAME]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['company_info'].find(qc, {TAG_NAME: 1, TAG_COMPANY_CODE: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find company, condition = %s, err = %s", query_condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['company_info'].find(qc, {TAG_NAME: 1, TAG_COMPANY_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(query_condition[Q_OFFSET])).limit(int(query_condition[Q_LIMIT]))

            company_list = []
            for one_company in results.__iter__():
                if "_id" in one_company.keys():
                    del one_company["_id"]

                one_company['herf'] = '/term_companys/' + one_company[TAG_COMPANY_CODE]
                company_list.append(one_company)

            resp = {
                Q_LIMIT: int(query_condition[Q_LIMIT]),
                Q_OFFSET: int(query_condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_COMPANYS: company_list
            }
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('query_c = %s, Exception = %s', query_condition, err)

    return resp


def query_term_company_detail(httpinstance, company_code):
    """
    查询厂商详细信息
    :param httpinstance:
    :param company_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['company_info'].find_one({TAG_COMPANY_CODE: company_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered company"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_term_company_detail fail!, company_code = %s, e = %s', company_code, err)

    return resp
