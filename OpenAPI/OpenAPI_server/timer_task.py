# -*- coding: utf-8 -*-
__author__ = 'jxh'


from common.api_tagdef import *
from common.mongo_utils import *
from common.auth_utils import resource_auth
from common.resouce_type import RESOURCE_TIMERTASK
from common.iot_request_handler import IotRequestHandler
from OpenAPI_server.http_utils import *
from common.settings import PORTAL_API_URL
import  json

PORTAL_API_TIMERTASK_URL = PORTAL_API_URL + 'timertask'

# 传感器列表信息查询
class TimerTaskList(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        """
        查询符合条件的定时任务列表
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, default=''), RESOURCE_TIMERTASK, None, self.get_argument(TAG_APPID, default=''))
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
            resp = query_timertasks(self, condition)
            self.write(resp)
            self.finish()
            logging.info('query_timertasks, condition = %s, result = %s', condition, resp)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_timertask fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self):
        """
        插入定时任务
        """
        try:
            logging.info("Get insert timer_task require:")
            reqbody = self.request.body.decode()
            bodydict = json.loads(reqbody)
            bodydict[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)
            http_client_post(bodydict, "add", self, PORTAL_API_TIMERTASK_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('insert_timertask fail! err = %s', err)


# 传感器详细信息查询
class TimerTaskInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, task_code):
        """
        获取单个定时任务详细信息
        :param task_code: 传感器编号
        """
        try:
            # 资源访问权限校验
            searched_appkey = resource_auth(self.request.headers.get(TAG_APPKEY, ''), RESOURCE_TIMERTASK, task_code,
                                            self.get_argument(TAG_APPID, default=''))
            if searched_appkey is None:
                self.set_status(401)
                self.write({"status": 1000, "status_text": "Resource access request is not authorized"})
                self.finish()
                return

            resp = query_timertask_detail(self, task_code)
            logging.info('query_timertask_detail, task_code = %s, result = %s', task_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_timertasks_detail fail! err = %s', err)

    @tornado.web.asynchronous
    def post(self, taskcode):
        """
        修改定时任务信息
        :param taskcode:定时任务编码
        """
        try:
            logging.info("Get update sensor info require")
            # 获取request 内容
            reqbody = self.request.body.decode()
            timertaskinfo = json.loads(reqbody)

            # 增加appkey到请求报文
            timertaskinfo[TAG_APPKEY] = self.request.headers.get(TAG_APPKEY)

            # 报文增加sensornode_code
            timertaskinfo[TAG_SENSOR_CODE] = taskcode
            http_client_post(timertaskinfo, "edit", self, PORTAL_API_TIMERTASK_URL)
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('update tasktimer info failed! err = %s', err)

    @tornado.web.asynchronous
    def delete(self, taskcode):
        """
        删除传感器信息
        :param taskcode:定时任务编码
        """
        try:
            logging.info("Get delete timertask require")
            # 获取request 内容
            tasktimerinfo = {TAG_SENSOR_CODE: taskcode, TAG_APPKEY: self.request.headers.get(TAG_APPKEY)}

            # 调用门户api完成实际操作, 在http_client_post中会进行返回响应关闭连接操作，此处不必处理
            http_client_post(tasktimerinfo, "delete", self, PORTAL_API_TIMERTASK_URL)
        except Exception as err:
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('delete timertask failed! err = %s', err)



def query_timertasks(httpinstance, condition):
    """
    定时器列表查询
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
        count = mongo_cli[DB_IOT]['op_schedule'].find(qc, {TAG_TIMERTASK_CODE: 1, TAG_NAME: 1, "reqtype": 1, "_id": 0}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find timertask_info, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['op_schedule'].find(qc, {TAG_NAME: 1, TAG_TIMERTASK_CODE: 1,"reqtype": 1, "_id": 1})\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT])).sort("_id", pymongo.DESCENDING)

            timertask_list = []
            for one_timerTask in results.__iter__():
                if "reqtype" in one_timerTask:
                    one_timerTask[TAG_TYPE] = one_timerTask["reqtype"]
                    del one_timerTask["reqtype"]
                if "_id"  in one_timerTask:
                    del one_timerTask["_id"]
                one_timerTask['herf'] = '/timertask/' + one_timerTask[TAG_TIMERTASK_CODE]
                timertask_list.append(one_timerTask)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_TIMERTASK: timertask_list
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


def query_timertask_detail(httpinstance, task_code):
    """
    查询定时任务详细信息
    :param httpinstance:
    :param task_code: 定时任务编码
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['op_schedule'].find_one({TAG_TIMERTASK_CODE: task_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered pos"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_timertask_detail fail!, sensor_code = %s, e = %s', task_code, err)

    return resp