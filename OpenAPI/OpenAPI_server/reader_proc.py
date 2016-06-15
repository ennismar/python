# -*- coding: utf-8 -*-
__author__ = 'neo'

import json
import tornado.web

from common.iot_msg import *
from common.msgtypedef import *
from common.eventno import *
from common.iot_procdef import *
from common.mongo_utils import *
from common.api_tagdef import *
from OpenAPI_server.http_utils import http_client_pool, http_client_post
from OpenAPI_server.serv_zmq_cfg import stream_procs
from common.auth_utils import resource_auth
from common.settings import PORTAL_API_URL
from common.resouce_type import RESOURCE_READER
from common.iot_request_handler import IotRequestHandler


# 门户api接口reader操作url
PORTAL_API_READER_URL = PORTAL_API_URL + 'reader'


# 读写器查询
class ReadersUtils(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的readers列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_READER, None,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            condition = {
                TAG_READER_NAME: self.get_argument(TAG_READER_NAME, default=''),
                TAG_READER_TYPE: self.get_argument(TAG_READER_TYPE, default=''),
                TAG_COMPANY_CODE: self.get_argument(TAG_COMPANY_CODE, default=''),
                TAG_TERM_CODE: self.get_argument(TAG_TERM_CODE, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
                TAG_APPKEY: searched_appkey,
            }
            resp = query_readers(self, condition)
            logging.info('query_readers, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_readers fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self):
        """
        新增一个reader信息
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            reader_info = json.loads(req_body)

            # 增加appkey到请求报文
            reader_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 校验reader_info合法性
            ret, err = reader_info_check(self, reader_info)
            if ret is not True:
                self.write({"status": 1000, "status_text": err})
                self.finish()
                logging.error('reader_info_check fail! err = %s', err)
            else:
                # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
                http_client_post(reader_info, "add", self, PORTAL_API_READER_URL)
        except Exception as err:
            logging.error('add reader info fail! err = %s', err)
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


# 读写器详细信息查询
class ReaderInfoReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, reader_code):
        """
        获取单个reader详细信息
        :param reader_code:
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_READER, reader_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_reader_detail(self, reader_code)
            logging.info('query_reader_detail, reader_code = %s, result = %s', reader_code, resp)
            self.write(resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            logging.error('query_readers_detail fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self, reader_code):
        """
        修改单个reader信息
        :param reader_code:
        """
        try:
            # 获取request 内容
            req_body = self.request.body.decode()
            reader_info = dict(json.loads(req_body))

            # 增加appkey到请求报文
            reader_info[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 报文增加reader_code
            reader_info[TAG_READER_CODE] = reader_code

            # 校验reader_code合法性
            ret, err = check_reader_code(self, reader_info[TAG_READER_CODE])
            if ret is not True:
                self.write({"status": 1000, "status_text": err})
                self.finish()
                logging.error('reader_info_check fail! err = %s', err)
            else:
                # 校验reader_info合法性
                ret, err = reader_info_check(self, reader_info)
                if ret is not True:
                    self.write({"status": 1000, "status_text": err})
                    self.finish()
                    logging.error('reader_info_check fail! err = %s', err)
                else:
                    # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
                    http_client_post(reader_info, "edit", self, PORTAL_API_READER_URL)
        except Exception as err:
            logging.error('update reader info fail! err = %s', err)
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()


    @tornado.web.asynchronous
    def delete(self, reader_code):
        """
        删除一个reader信息
        :param reader_code:
        """
        try:
            # 获取request 内容
            reader_info = {'reader_code': reader_code, TAG_APPKEY: self.request.headers.get(TAG_APPKEY)}

            # 增加appkey到请求报文

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(reader_info, "delete", self, PORTAL_API_READER_URL)
        except Exception as err:
            logging.error('delete reader info fail! err = %s', err)
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


# 获取reader taglist
class ReaderGetTagListReq(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    @tornado.web.asynchronous
    def get(self, reader_code):
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_READER, reader_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            ret, msg = pack_get_reader_tag_list_req(self, self._linkid, reader_code, self.request.headers.get(TAG_IOT_H_TRANSID, ''))
            if ret is True:
                # 缓存当前http client
                http_client_pool[self._linkid] = self

                # 发送消息给处理机
                if IOT_PROC_READER_CTRL in stream_procs.keys():
                    stream_procs[IOT_PROC_READER_CTRL].send(msg)
                    logging.debug('Send Read Taglist Req Succ! linkid = %d, reader_code = %s', self._linkid, reader_code)
                else:
                    logging.error("Can't find process = %s", IOT_PROC_READER_CTRL)
                    self.write({"status": 1000, "status_text": "Internal system error"})
                    self.finish()
            else:
                self.write({"status": 1000, "status_text": msg})
                self.finish()
                logging.error('pack_get_reader_tag_list_req fail! linkid = %d, reader_code = %s', self._linkid, reader_code)
        except Exception as err:
            self.set_status(500)
            logging.error('Send Req to %s fail! err = %s', IOT_PROC_READER_CTRL, err)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


# 读写器参数操作
class ReaderParams(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    @tornado.web.asynchronous
    def get(self, reader_code, param_type):
        """
        获取读写器参数
        :param param_type:
        :param reader_code:
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_READER, reader_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            ret, msg = get_reader_params(self, self._linkid, reader_code, param_type, self.request.headers.get(TAG_IOT_H_TRANSID, ''))
            if ret is True:
                # 缓存当前http client
                http_client_pool[self._linkid] = self

                # 发送消息给处理机
                if IOT_PROC_READER_CTRL in stream_procs.keys():
                    stream_procs[IOT_PROC_READER_CTRL].send(msg)
                    logging.debug('Send GET_READER_PARAMS Req Succ! linkid = %d, reader_code = %s', self._linkid, reader_code)
                else:
                    logging.error("Can't find process = %s", IOT_PROC_READER_CTRL)
                    self.write({"status": 1000, "status_text": "Internal system error"})
                    self.finish()
            else:
                self.write({"status": 1000, "status_text": msg})
                self.finish()
                logging.error('GET_READER_PARAMS fail! linkid = %d, reader_code = %s, err = %s', self._linkid, reader_code, msg)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('GET_READER_PARAMS fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self, reader_code, param_type):
        """
        设置读写器参数
        :param param_type: 保持和url参数配置一致，本方法中无用
        :param reader_code:
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_READER, reader_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            req_body = str(self.request.body.decode())
            if req_body == "":
                logging.error("request body is NULL, reader_code = %s", reader_code)
                self.write({"status": 1000, "status_text": "request body is NULL"})
                self.finish()
            else:
                try:
                    req_dict = json.loads(req_body)
                except Exception:
                    resp = 'Req body is invalid! body = %s' % req_body
                    self.set_status(500)
                    self.write({"status": 1000, "status_text": resp})
                    self.finish()
                    logging.error(resp)
                    return

                ret, msg = set_reader_params(self, self._linkid, reader_code, req_dict, MSGTYPE_READER_SET_PARAM_REQ,
                                             self.request.headers.get(TAG_IOT_H_TRANSID, ''))
                if ret is True:
                    # 缓存当前http client
                    http_client_pool[self._linkid] = self

                    # 发送消息给处理机
                    if IOT_PROC_READER_CTRL in stream_procs.keys():
                        stream_procs[IOT_PROC_READER_CTRL].send(msg)
                        logging.debug('Send GET_READER_PARAMS Req Succ! linkid = %d, reader_code = %s', self._linkid, reader_code)
                    else:
                        logging.error("Can't find process = %s", IOT_PROC_READER_CTRL)
                        self.write({"status": 1000, "status_text": "Internal system error"})
                        self.finish()
                else:
                    self.write({"status": 1000, "status_text": msg})
                    self.finish()
                    logging.error('SET_READER_PARAMS fail! linkid = %d, reader_code = %s', self._linkid, reader_code)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('SET_READER_PARAMS fail! err = %s', err)

    def on_finish(self):
        try:
            del http_client_pool[self._linkid]
        except Exception:
            # 有可能finish时，link还没有加入http_client_pool，del有可能异常，无需处理
            pass


# 写tag epc和userdata
class ReaderProgTag(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    @tornado.web.asynchronous
    def post(self, reader_code):
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_READER, reader_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            req_body = str(self.request.body.decode())
            if req_body == "":
                logging.warning("request body is NULL, reader_code = %s", reader_code)
                self.write({"status": 1000, "status_text": "request body is NULL"})
                self.finish()
                return

            ret, msg = get_reader_proc_tag_msg(self, self._linkid, reader_code, req_body, self.request.headers.get(TAG_IOT_H_TRANSID, ''))
            if ret is True:
                # 缓存当前http client
                http_client_pool[self._linkid] = self

                # 发送消息给处理机
                if IOT_PROC_READER_CTRL in stream_procs.keys():
                    stream_procs[IOT_PROC_READER_CTRL].send(msg)
                    logging.debug('Send Prog TAG Req Succ! linkid = %d, reader_code = %s', self._linkid, reader_code)
                else:
                    logging.error("Can't find process = %s", IOT_PROC_READER_CTRL)
                    self.write({"status": 1000, "status_text": "Internal system error"})
                    self.finish()
            else:
                self.write({"status": 1000, "status_text": msg})
                self.finish()
                logging.error('Prog TAG fail! linkid = %d, reader_code = %s, err = %s', self._linkid, reader_code, msg)
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
            pass


def get_term_code_by_reader_code(httpinstance, db_name, collection, reader_code):
    """
    根据reader_code获取对应的term_code
    :param httpinstance:
    :param db_name:
    :param collection:
    :param reader_code:
    :return:
    """
    try:
        return True, mongo_cli[db_name][collection].find_one({TAG_READER_CODE: reader_code})[TAG_TERM_CODE]
    except Exception as err:
        httpinstance.set_status(500)
        logging.error("Can't find term_code by reader_code! db = %s.%s, reader_code = %s, err = %s", db_name, collection, reader_code, err)
        return False, ""


def pack_get_reader_tag_list_req(httpinstance, linkid, reader_code, trans_id):
    """
    生成获取taglist的消息
    :param httpinstance:
    :param linkid:
    :param reader_code:
    :param trans_id
    :return:
    """
    try:
        # 获取term_code
        ret, term_code = get_term_code_by_reader_code(httpinstance, DB_IOT, 'reader_info', reader_code)
        logging.debug('reader_code = %s, term_code = %s', reader_code, term_code)
        if ret is False:
            return False, "unregistered reader"

        req_dict = {TAG_READER_CODE: reader_code}
        msg = pack_full_msg(linkid, MSGTYPE_READER_GET_TAGLIST_DATA_REQ, json.dumps(req_dict),
                            IOT_PROC_READER_CTRL, IOT_EVENT_READER, term_code, reader_code, trans_id)
        return True, msg
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('pack_get_reader_tag_list_req fail! err = %s', err)
        return False, "Internal system error"


def query_readers(httpinstance, condition):
    """
    读写器列表查询
    :param httpinstance:
    :param condition:
    """
    resp = ''

    qc = {}
    if condition[TAG_READER_NAME] != '':
        qc[TAG_READER_NAME] = condition[TAG_READER_NAME]

    if condition[TAG_READER_TYPE] != '':
        qc[TAG_READER_TYPE] = condition[TAG_READER_TYPE]

    if condition[TAG_COMPANY_CODE] != '':
        qc[TAG_COMPANY_CODE] = condition[TAG_COMPANY_CODE]

    if condition[TAG_TERM_CODE] != '':
        qc[TAG_TERM_CODE] = condition[TAG_TERM_CODE]

    qc[TAG_APPKEY] = condition[TAG_APPKEY]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['reader_info'].find(qc, {TAG_READER_NAME: 1, TAG_READER_CODE: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find reader_info, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['reader_info'].find(qc, {TAG_READER_NAME: 1, TAG_READER_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            reader_list = []
            for one_reader in results.__iter__():
                if "_id" in one_reader.keys():
                    del one_reader["_id"]

                one_reader['herf'] = '/readers/' + one_reader[TAG_READER_CODE]
                reader_list.append(one_reader)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_READERS: reader_list
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


def query_reader_detail(httpinstance, reader_code):
    """
    查询读写器详细信息
    :param httpinstance:
    :param reader_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['reader_info'].find_one({TAG_READER_CODE: reader_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered reader"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_reader_detail fail!, reader_code = %s, e = %s', reader_code, err)

    return resp


def get_reader_params(httpinstance, linkid, reader_code, param_type, trans_id):
    """
    获取读写器参数
    :param httpinstance:
    :param linkid:
    :param reader_code:
    :param param_type:
    :param trans_id:
    :return:
    """
    try:
        # 根据获取参数类型，对应系统msgtype
        if param_type == "":
            param_type = MSGTYPE_READER_GET_PARAMS_REQ
        elif param_type == "/general":
            param_type = MSGTYPE_READER_GET_GENERAL_REQ
        elif param_type == "/network":
            param_type = MSGTYPE_READER_GET_NETWORK_REQ
        elif param_type == "/time":
            param_type = MSGTYPE_READER_GET_TIME_REQ
        elif param_type == "/taglist":
            param_type = MSGTYPE_READER_GET_TAGLIST_CFG_REQ
        elif param_type == "/qcquire":
            param_type = MSGTYPE_READER_GET_QCQUIRE_REQ
        elif param_type == "/ioports":
            param_type = MSGTYPE_READER_GET_IOPORTS_REQ
        elif param_type == "/automode":
            param_type = MSGTYPE_READER_GET_AUTOMODE_REQ
        elif param_type == "/notify":
            param_type = MSGTYPE_READER_GET_NOTIFY_REQ
        else:
            resp = "Can't support get param_type = %s" % param_type
            logging.error(resp)
            return False, resp

        # 获取term_code
        ret, term_code = get_term_code_by_reader_code(httpinstance, 'iot', 'reader_info', reader_code)
        logging.debug('reader_code = %s, term_code = %s', reader_code, term_code)
        if ret is False:
            return False, "unregistered reader"

        req_dict = {TAG_READER_CODE: reader_code}
        msg = pack_full_msg(linkid, param_type, json.dumps(req_dict), IOT_PROC_READER_CTRL, IOT_EVENT_READER, term_code, reader_code, trans_id)
        return True, msg
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('get_reader_params fail! err = %s', err)
        return False, "Internal System Error"


def set_reader_params(httpinstance, linkid, reader_code, params, msgtype, trans_id):
    """
    设置读写器参数
    :param httpinstance:
    :param msgtype:
    :param linkid:
    :param reader_code:
    :param trans_id
    :param params:
    """
    try:
        # 获取term_code
        ret, term_code = get_term_code_by_reader_code(httpinstance, DB_IOT, 'reader_info', reader_code)
        logging.debug('reader_code = %s, term_code = %s', reader_code, term_code)
        if ret is False:
            return False, "unregistered reader"

        msg = pack_full_msg(linkid, msgtype, json.dumps(params), IOT_PROC_READER_CTRL, IOT_EVENT_READER, term_code, reader_code, trans_id)
        return True, msg
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('set_reader_params fail! err = %s', err)
        return False, "Internal System error!"


def get_reader_proc_tag_msg(httpinstance, linkid, reader_code, msg_body, trans_id):
    """
    组包写tag iot消息
    :param httpinstance:
    :param linkid:
    :param reader_code:
    :param msg_body:
    :param trans_id
    :return:
    """
    try:
        # 解析命令
        req_dict = json.loads(msg_body)
        cmd = list(req_dict.keys())[0]
        value = req_dict[cmd]

        # 协议命令转msgtype
        if cmd.lower() == PROGRAM_EPC:
            msgtype = MSGTYPE_READER_PROG_EPC_REQ
        elif cmd.lower() == PROGRAM_USER_DATA:
            msgtype = MSGTYPE_READER_PROG_USERDATA_REQ
        else:
            resp = "Unsupported program command! cmd = %s" % cmd
            return False, resp

        # 消息体
        iot_req = {
            TAG_COMMANDS: cmd.lower() + '=' + value
        }

        # 获取term_code
        ret, term_code = get_term_code_by_reader_code(httpinstance, DB_IOT, 'reader_info', reader_code)
        logging.debug('reader_code = %s, term_code = %s', reader_code, term_code)
        if ret is False:
            return False, "unregistered reader"

        msg = pack_full_msg(linkid, msgtype, json.dumps(iot_req), IOT_PROC_READER_CTRL, IOT_EVENT_READER, term_code, reader_code, trans_id)
        return True, msg
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('get_reader_params fail! err = %s', err)
        return False, "Internal System Error"


def reader_info_check(httpinstance, reader_info):
    """
    reader信息合法性校验
    :param httpinstance:
    :param reader_info:
    :return:
    """
    # 校验读写器类型
    if TAG_READER_TYPE in reader_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['dictionary'].find({TAG_DICT_VALUE: reader_info[TAG_READER_TYPE], TAG_DICT_TYPE: TAG_READER_TYPE}).count()
            if ret == 0:
                return False, "unsupported reader type"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check reader_type fail!, reader_code = %s, e = %s', reader_info['reader_type'], err)
            return False, "Internal System Error"
    # else:
    #     return False, TAG_READER_TYPE + " is None"

    # 校验读写器厂商
    if TAG_COMPANY_CODE in reader_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['company_info'].find({TAG_COMPANY_CODE: reader_info[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "unsupported company"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check company fail!, company_code = %s, e = %s', reader_info['company_code'], err)
            return False, "Internal System Error"
    else:
        return False, TAG_COMPANY_CODE + " is None"

    # 校验读写器型号
    if TAG_TERM_CODE in reader_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['term_model_info'].find({TAG_TERM_CODE: reader_info[TAG_TERM_CODE], TAG_COMPANY_CODE: reader_info[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "term_code is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check term_code fail!, term_code = %s, e = %s', reader_info[TAG_TERM_CODE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_TERM_CODE + " is None"

    # 校验网关信息, optional
    if TAG_GATEWAY_CODE in reader_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['gateway_info'].find({TAG_GATEWAY_CODE: reader_info[TAG_GATEWAY_CODE], TAG_GATEWAY_NAME: reader_info[TAG_GATEWAY_NAME]}).count()
            if ret == 0:
                return False, "gate_code or gate_name is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check term_code fail!, gate_code = %s, gate_name = %s, e = %s', reader_info[TAG_GATEWAY_CODE], reader_info[TAG_GATEWAY_NAME], err)
            return False, "Internal System Error"

    # 校验mac
    if TAG_MAC_ADDR not in reader_info.keys():
        return False, "mac address is None"

    # 校验状态
    if TAG_STATUS in reader_info.keys():
        try:
            ret = mongo_cli[DB_IOT]['dictionary'].find({TAG_DICT_VALUE: str(reader_info[TAG_STATUS]), TAG_DICT_TYPE: TAG_STATUS}).count()
            if ret == 0:
                return False, "status is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check status fail!, status = %s, e = %s', reader_info[TAG_STATUS], err)
            return False, "Internal System Error"
    else:
        return False, TAG_STATUS + " is None"

    # 校验连接信息
    if TAG_GATEWAY_CODE not in reader_info.keys():
        if TAG_CONNECTION not in reader_info.keys():
            return False, "connection information is None"

    return True, ""


# 校验reader_code
def check_reader_code(httpinstance, reader_code):
    """

    :param httpinstance:
    :param reader_code:
    :return:
    """
    try:
        ret = mongo_cli[DB_IOT]['reader_info'].find({TAG_READER_CODE: reader_code}).count()
        if ret == 0:
            return False, "reader_code is invalid"
        else:
            return True, ""
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('check_reader_code fail!, reader_code = %s, e = %s', reader_code, err)
        return False, "Internal System Error"
