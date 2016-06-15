# -*- coding: utf-8 -*-
__author__ = 'neo'

import json

import tornado.web

from OpenAPI_server.http_utils import http_client_pool, http_client_post
from common.api_tagdef import *
from common.auth_utils import resource_auth
from common.iot_request_handler import IotRequestHandler
from common.mongo_utils import *
from common.resouce_type import RESOURCE_APP_DATA
from common.settings import PORTAL_API_URL
from common.str_parse_utils import parse_query_conditions, parse_query_result_tag_list

# 门户api接口reader操作url
PORTAL_API_APP_DATA_URL = PORTAL_API_URL + 'appdata'


def query_app_data(handler, condition):
    """
    完成对app data的客户自定义查询
    :param handler:
    :param condition:
    :return:
    """
    resp = ''

    # 查询条件
    if condition[TAG_QUERY_CONDITIONS] == '':
        qc = {}
    else:
        try:
            qc = parse_query_conditions(condition[TAG_QUERY_CONDITIONS])
        except Exception as err:
            logging.error('Conditions is invalid! err = %s, conditions = %s', err, condition[TAG_QUERY_CONDITIONS])
            handler.set_status(501)
            return {"status": 1000, "status_text": "Conditions is invalid!"}

    # 添加资源的appkey
    qc[TAG_APPKEY]  = condition[TAG_APPKEY]

    # 返回字段
    result_tags = parse_query_result_tag_list(condition[TAG_QUERY_RESULT_TAG_LIST])

    # TAG_DATA_CODE 默认加入返回列
    if TAG_DATA_CODE not in result_tags.keys():
        result_tags[TAG_DATA_CODE] = 1

    # # 不返回mongodb的oid
    # result_tags['_id'] = 0

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['app_data'].find(qc, result_tags).count()
    except Exception as err:
        logging.info("Can't find app_data, condition = %s, err = %s", condition, err)
        handler.set_status(501)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['app_data'].find(qc, result_tags).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            result_list = []
            for one_result in results.__iter__():
                if "_id" in one_result.keys():
                    del one_result["_id"]

                # 转换结果的datetime类型为string
                # dict_datetime_to_string(one_result)
                result_list.append(one_result)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_DATA_INFO: result_list
            }
        except Exception as err:
            handler.set_status(501)
            logging.error('query_c = %s, Exception = %s', condition, err)
    else:
        resp = {
            Q_LIMIT: int(condition[Q_LIMIT]),
            Q_OFFSET: int(condition[Q_OFFSET]),
            Q_TOTAL: 0
        }

    return resp


class AppDataUtils(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        根据外部应用自己设置的条件查询列表

        比较字符：大于 -- $gt，大于等于 -- $gte
                  小于 -- $lt，小于等于 -- $lte

        查询条件以json格式，进行url encode后放入url conditions中

        result_tag_list:需要返回的字段列表，以英文逗号’,’分割
        格式：result_tag_list=字段1，字段2...
        例如：查询属于中国，创建事件是2015年1月1日到2015年2月1日之间的资源，返回资源名称，地址两个字段
        https://api.rozen.cn/v1/app_data?conditions=%7B%22country%22%3A%20%22china%22%2C%22createdate%22%3A%20%7B%22%24gte%22%3A%20%222015-01-01%2000%3A00%3A00%22%2C%22%24lte%22%3A%20%222015-02-01%2000%3A00%3A00%22%7D%7D&result_tag_list=name,address&offset=0&limit=20

        注：时间格式为YYYY-MM-DD HH24:MI:SS
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_APP_DATA, None,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                return

            condition = {
                TAG_QUERY_CONDITIONS: self.get_argument(TAG_QUERY_CONDITIONS, default=''),
                TAG_QUERY_RESULT_TAG_LIST: self.get_argument(TAG_QUERY_RESULT_TAG_LIST, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey,
            }
            resp = query_app_data(self, condition)
            logging.info('query_app_data, condition = %s, result = %s', condition, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(501)
            logging.error('query app_data fail! err = %s', err)
            self.write({"status": 1000, "status_text": "Internal system error"})

    @tornado.web.asynchronous
    def post(self):
        """
        新增一个应用数据
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            logging.info('Add app_data = %s', req_body)
            data_info = json.loads(req_body)

            # 增加appkey到请求报文
            data_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(data_info, "add", self, PORTAL_API_APP_DATA_URL)
        except Exception as err:
            logging.error('add app_data fail! err = %s', err)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


class AppDataOneTagUtils(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, data_code):
        """
        查询特定的一个app data详细信息
        :param data_code:
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_APP_DATA, data_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_app_data_detail(self, data_code)
            logging.info('query_app_data_detail, data_code = %s, result = %s', data_code, resp)
            self.write(resp)
        except Exception as err:
            logging.error('edit app_data fail! err = %s', err)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})

    @tornado.web.asynchronous
    def post(self, data_code):
        """
        修改一个app_data数据
        :param data_code:
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            data_info = json.loads(req_body)

            # 增加appkey到请求报文
            data_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)
            data_info[TAG_DATA_CODE] = data_code

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(data_info, "edit", self, PORTAL_API_APP_DATA_URL)
        except Exception as err:
            logging.error('edit app_data fail! err = %s', err)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})

    @tornado.web.asynchronous
    def delete(self, data_code):
        """
        删除一个app data数据
        :param data_code:
        """
        try:
            # 获取request 内容
            # 增加appkey到请求报文
            data_info = {
                TAG_APPKEY: self.request.headers.get(TAG_APPKEY),
                TAG_DATA_CODE: data_code
            }

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(data_info, "delete", self, PORTAL_API_APP_DATA_URL)
        except Exception as err:
            logging.error('delete app_data fail! err = %s', err)
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


def query_app_data_detail(handler, data_code):
    """
    查询app_data详细信息
    :param handler:
    :param data_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['app_data'].find_one({TAG_DATA_CODE: data_code}, {TAG_DATA_INFO: 1, "_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered app_data"}
        else:
            resp = info
    except Exception as err:
        handler.set_status(501)
        logging.error('query_app_data_detail fail!, data_code = %s, e = %s', data_code, err)

    return resp