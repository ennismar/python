# -*- coding: utf-8 -*-
__author__ = 'Administrator'


from common.api_tagdef import *
from common.mongo_utils import *
from common.auth_utils import resource_auth
from common.resouce_type import RESOURCE_SENSOR
from common.iot_request_handler import IotRequestHandler
from OpenAPI_server.http_utils import *
from common.settings import PORTAL_API_URL
import  json

PORTAL_API_SENSOR_URL = PORTAL_API_URL + 'sensor'

# 传感器列表信息查询
class SensorList(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的传感器列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_SENSOR, None, self.get_argument(TAG_APPID, default=''))
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
            resp = query_sensors(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_sensors, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sensors fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self):
        """
        插入传感器
        """
        try:
            logging.info("Get insert sensor require:")
            reqbody = self.request.body.decode()
            bodydict = json.loads(reqbody)
            bodydict[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)
            http_client_post(bodydict, "add", self, PORTAL_API_SENSOR_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('insert_sensornode fail! err = %s', err)


# 传感器详细信息查询
class SensorInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, sensor_code):
        """
        获取单个传感器详细信息
        :param sensor_code: 传感器编号
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_SENSOR, sensor_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_sensor_detail(self, sensor_code)
            logging.info('query_sensor_detail, sensor_code = %s, result = %s', sensor_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_sensor_detail fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self,sensorcode):
        """
        修改传感器信息
        :param sensorcode:传感器编号
        """
        try:
            logging.info("Get update sensor info require")
            # 获取request 内容
            reqbody = self.request.body.decode()
            sensorinfo = json.loads(reqbody)

            # 增加appkey到请求报文
            sensorinfo[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 报文增加sensornode_code
            sensorinfo[TAG_SENSOR_CODE] = sensorcode
            http_client_post(sensorinfo, "edit", self, PORTAL_API_SENSOR_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('update sensor info failed! err = %s', err)

    @tornado.web.asynchronous
    def delete(self, sensorcode):
        """
        删除传感器信息
        :param sensorcode:传感器编号
        """
        try:
            logging.info("Get delete sensorinfo require")
            # 获取request 内容
            sensorinfo = {TAG_SENSOR_CODE: sensorcode, TAG_APPKEY: self.request.headers.get(TAG_APPKEY)}

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(sensorinfo, "delete", self, PORTAL_API_SENSOR_URL)
        except Exception as err:
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('delete sensorinfo failed! err = %s', err)



def query_sensors(httpinstance, condition):
    """
    传感器列表查询
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
        count = mongo_cli[DB_IOT]['sensor_info'].find(qc, {TAG_SENSOR_CODE: 1, TAG_NAME: 1, "sensor_type": 1, "_id": 0}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find sensor_info, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['sensor_info'].find(qc, {TAG_NAME: 1, TAG_SENSOR_CODE: 1,"sensor_type": 1, "_id": 1})\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT])).sort("_id", pymongo.DESCENDING)

            sensor_list = []
            for one_sensor in results.__iter__():
                if "sensor_type" in one_sensor:
                    one_sensor[TAG_TYPE] = one_sensor["sensor_type"]
                    del one_sensor["sensor_type"]
                if "_id"  in one_sensor:
                    del one_sensor["_id"]
                one_sensor['herf'] = '/sensor/' + one_sensor[TAG_SENSOR_CODE]
                sensor_list.append(one_sensor)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_SENSOR: sensor_list
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


def query_sensor_detail(httpinstance, sensor_code):
    """
    查询传感器详细信息
    :param httpinstance:
    :param sensor_code: 传感器编码
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['sensor_info'].find_one({TAG_SENSOR_CODE: sensor_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered pos"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_sensor_detail fail!, sensor_code = %s, e = %s', sensor_code, err)

    return resp

def insert_check(httpinstance, sensorinfo):
    """
    插入时检查传感器信息的有效性
    :param sensorinfo:
    :param httpinstance:
    :return:
    """

    # 检验传感节点
    if TAG_OWN_CODE in sensorinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['sensornode_info'].find({TAG_SENSORNODE_CODE: sensorinfo[TAG_OWN_CODE]}).count()
            if ret == 0:
                logging.info(mongo_cli[DB_IOT]['sensornode_info'])
                logging.info({TAG_SENSORNODE_CODE: sensorinfo[TAG_OWN_CODE]})
                return False, "sensornode not register"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check sensornode fail!, company_code = %s, e = %s', sensorinfo[TAG_OWN_CODE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_OWN_CODE + " is None"

    # 校验传感器厂商
    if TAG_COMPANY_CODE in sensorinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['company_info'].find({TAG_COMPANY_CODE: sensorinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "unsupported company"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check company fail!, company_code = %s, e = %s', sensorinfo[TAG_COMPANY_CODE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_COMPANY_CODE + " is None"

    # 校验读写器型号
    if TAG_TERM_CODE in sensorinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['term_model_info'].find({TAG_TERM_CODE: sensorinfo[TAG_TERM_CODE], TAG_COMPANY_CODE: sensorinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "term_code is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check term_code fail!, term_code = %s, e = %s', sensorinfo[TAG_TERM_CODE], err)
            return False, "Internal System Error"
    else:
        return False, TAG_TERM_CODE + " is None"

    return True, ""

def update_check(httpinstance, sensorinfo):
    """
    更新检查传感器信息的有效性
    :param httpinstance:
    :param sensorinfo:消息节点信息
    :return:
    """

    # 检验传感节点
    if TAG_OWN_CODE in sensorinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['sensornode_info'].find({TAG_SENSORNODE_CODE: sensorinfo[TAG_OWN_CODE]}).count()
            if ret == 0:
                logging.error( mongo_cli[DB_IOT]['sensornode_info'])
                logging.error({TAG_SENSORNODE_CODE: sensorinfo[TAG_OWN_CODE]})
                return False, "sensornode not register"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check sensornode fail!, company_code = %s, e = %s', sensorinfo[TAG_OWN_CODE], err)
            return False, "Internal System Error"


    # 校验传感器厂商
    if TAG_COMPANY_CODE in sensorinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['company_info'].find({TAG_COMPANY_CODE: sensorinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "unsupported company"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check company fail!, company_code = %s, e = %s', sensorinfo[TAG_COMPANY_CODE], err)
            return False, "Internal System Error"

    # 校验读写器型号
    if TAG_TERM_CODE in sensorinfo.keys():
        try:
            ret = mongo_cli[DB_IOT]['term_model_info'].find({TAG_TERM_CODE: sensorinfo[TAG_TERM_CODE], TAG_COMPANY_CODE: sensorinfo[TAG_COMPANY_CODE]}).count()
            if ret == 0:
                return False, "term_code is invalid"
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('check term_code fail!, term_code = %s, e = %s', sensorinfo[TAG_TERM_CODE], err)
            return False, "Internal System Error"

    return True, ""

def sensor_existed(httpinstance, sensorcode):
    """
    判断传感器是否存在
    :param httpinstance:
    :param sensorcode:消息节点信息
    :return:
    """
    try:
        ret = mongo_cli[DB_IOT]['sensor_info'].find({TAG_SENSOR_CODE: sensorcode}).count()
        if ret == 0:
            return False, "sensor_code is invalid"
        else:
            return True, ""
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('check sensorcode fail!, sensor_code = %s, e = %s', sensorcode, err)
        return False, "Internal System Error"