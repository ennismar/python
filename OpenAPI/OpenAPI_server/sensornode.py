# -*- coding: utf-8 -*-
__author__ = 'Administrator'


from common.api_tagdef import *
from common.mongo_utils import *
from common.auth_utils import resource_auth
from common.iot_request_handler import IotRequestHandler
from common.resouce_type import RESOURCE_SENSORNODE
from OpenAPI_server.http_utils import *
import  json
from common.settings import PORTAL_API_URL

PORTAL_API_SENSORNODE_URL = PORTAL_API_URL + 'sensornode'

TAG_TYPE = "type"
# 传感节点列表信息查询
class SensorNodeList(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的传感节点列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_SENSORNODE, None, self.get_argument(TAG_APPID, default=''))
            logging.info("Self appkey"+self.request.headers.get(TAG_APPKEY))
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
            resp = query_sensor_nodes(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_sm_pos, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sm_pos fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self):
        """
        插入传感器节点
        """
        try:
            logging.info("Get insert sensornode require:")
            reqbody = self.request.body.decode()
            bodydict = json.loads(reqbody)
            bodydict[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)
            http_client_post(bodydict, "add", self, PORTAL_API_SENSORNODE_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('insert_sensornode fail! err = %s', err)


# 传感节点详细信息查询
class SensorNodeInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, node_code):
        """
        获取单个传感节点详细信息
        :param node_code: 传感节点编号
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_SENSORNODE, node_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_sensor_node_detail(self, node_code)
            logging.info('query_sensornode_detail, pos_code = %s, result = %s', node_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sensornode_detail fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self, nodecode):
        """
        修改传感节点信息
        :param nodecode:传感节点编号
        """

        try:
            logging.info("Get update sensornode require")
            # 获取request 内容
            reqbody = self.request.body.decode()
            sensornodeinfo = json.loads(reqbody)

            # 增加appkey到请求报文
            sensornodeinfo[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 报文增加sensornode_code
            sensornodeinfo[TAG_SENSORNODE_CODE] = nodecode
            http_client_post(sensornodeinfo, "edit", self, PORTAL_API_SENSORNODE_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('update_sensornode! err = %s', err)

    @tornado.web.asynchronous
    def delete(self, nodecode):
        """
        删除传感节点信息
        :param nodecode:
        """
        try:
            logging.info("Get delete sensornode require")
            # 获取request 内容
            sensornodeinfo = {TAG_SENSORNODE_CODE: nodecode, TAG_APPKEY: self.request.headers.get(TAG_APPKEY)}

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(sensornodeinfo, "delete", self, PORTAL_API_SENSORNODE_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('Prog TAG fail! err = %s', err)


def query_sensor_nodes(httpinstance, condition):
    """
    传感节点列表查询
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
        count = mongo_cli[DB_IOT]['sensornode_info'].find(qc, {TAG_SENSORNODE_CODE: 1, TAG_NAME: 1, "_id": 0}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find sensornode_info, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['sensornode_info'].find(qc, {TAG_NAME: 1, TAG_SENSORNODE_CODE: 1, "_id": 1})\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT])).sort("_id", pymongo.DESCENDING)

            sensornode_list = []
            for one_node in results.__iter__():
                if "_id" in one_node:
                    del one_node["_id"]
                one_node['herf'] = '/sensornode/' + one_node[TAG_SENSORNODE_CODE]
                sensornode_list.append(one_node)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_SENSORNODE: sensornode_list
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


def query_sensor_node_detail(httpinstance, node_code):
    """
    查询传感节点详细信息
    :param node_code:
    :param httpinstance:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['sensornode_info'].find_one({TAG_SENSORNODE_CODE: node_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered sensornode"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_sensornode_detail fail!, pos_code = %s, e = %s', node_code, err)

    return resp

def insert_check(httpinstance, sensornodeinfo):
    """
    插入检查传感器信息的有效性
    :param httpinstance:
    :param sensornodeinfo:消息节点信息
    :return:
    """

    # 校验读写器厂商
    if TAG_COMPANY_CODE in sensornodeinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['company_info'].find({TAG_COMPANY_CODE: sensornodeinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "unsupported company"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check company fail!, company_code = %s, e = %s', sensornodeinfo['company_code'], err)
            return False, "Internal System Error"
    else:
        return False, TAG_COMPANY_CODE + " is None"

    # 校验读写器型号
    if TAG_TERM_CODE in sensornodeinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['term_model_info'].find({TAG_TERM_CODE: sensornodeinfo[TAG_TERM_CODE], TAG_COMPANY_CODE: sensornodeinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "term_code is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check term_code fail!, term_code = %s, e = %s', sensornodeinfo[TAG_TERM_CODE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_TERM_CODE + " is None"

    return True, ""

def update_check(httpinstance, sensornodeinfo):
    """
    更新检查传感器信息的有效性
    :param httpinstance:
    :param sensornodeinfo:消息节点信息
    :return:
    """

    # 校验读写器厂商
    if TAG_COMPANY_CODE in sensornodeinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['company_info'].find({TAG_COMPANY_CODE: sensornodeinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "unsupported company"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check company fail!, company_code = %s, e = %s', sensornodeinfo['company_code'], err)
            return False, "Internal System Error"

    # 校验读写器型号
    if TAG_TERM_CODE in sensornodeinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['term_model_info'].find({TAG_TERM_CODE: sensornodeinfo[TAG_TERM_CODE], TAG_COMPANY_CODE: sensornodeinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "term_code is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check term_code fail!, term_code = %s, e = %s', sensornodeinfo[TAG_TERM_CODE], err)
            return False, "Internal System Error"

    return True, ""

def sensornode_existed(httpinstance, sensornodecode):
    """
    判断传感器是否存在
    :param sensornodecode:
    :param httpinstance:
    :return:
    """
    try:
        ret = mongo_cli[DB_IOT]['sensornode_info'].find({TAG_SENSORNODE_CODE: sensornodecode}).count()
        if ret == 0:
            return False, "sensornode_code is invalid"
        else:
            return True, ""
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('check sensornodecode fail!, sensor_code = %s, e = %s', sensornodecode, err)
        return False, "Internal System Error"