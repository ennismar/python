# -*- coding: utf-8 -*-
__author__ = 'neo'

from common.settings import API_VERSION
from OpenAPI_server.reader_proc import *
from OpenAPI_server.term_company import *
from OpenAPI_server.term_models import *
from OpenAPI_server.camera_proc import *
from OpenAPI_server.building_proc import *
from OpenAPI_server.gateway_proc import *
from OpenAPI_server.room_proc import *
from OpenAPI_server.sm_posinfo import *
from OpenAPI_server.sm_access_controller_info import *
from OpenAPI_server.sm_idcard_info import *
from OpenAPI_server.mms import *
from OpenAPI_server.sms import *
from OpenAPI_server.app_data_utils import *
from OpenAPI_server.sensornode import *
from OpenAPI_server.sensor import *
from OpenAPI_server.trigger_proc import *
from OpenAPI_server.timer_task import *
#from OpenAPI_server.mmspressuretester import *
from OpenAPI_server.mms_interface import *

# for test
from OpenAPI_server.test import ZeroMqTest, TestMsg, TestNotifyMsg, TestAuth, TagNotify, TestPerformance

# http server url配置
app_handlers = [
    # 测试
    (r'/z_test', ZeroMqTest),
    (r'/test', TestMsg),
    (r'/test_notify', TestNotifyMsg),
    (r'/test_auth/(.*)', TestAuth),
    (r'/performance', TestPerformance),

    # 手持机上报taglist
    (r'/api/readers/notify', TagNotify),

    # 基础信息查询
    # 厂商信息查询
    (API_VERSION + r'/term_companys', QueryTermCompanysReq),
    (API_VERSION + r'/term_companys/(.*)', QueryTermCompanyInfoReq),

    # 终端型号查询
    (API_VERSION + r'/term_models', QueryTermModels),
    (API_VERSION + r'/term_models/(.*)', QueryTermModelInfoReq),

    # 读写器相关
    # 读写器查询
    (API_VERSION + r'/readers', ReadersUtils),
    (API_VERSION + r'/readers/([^/]*)$', ReaderInfoReq),

    # 读写器参数
    (API_VERSION + r'/readers/(.*)\/params(.*)', ReaderParams),

    # 获取读写器taglist
    (API_VERSION + r'/readers/(.*)\/taglist', ReaderGetTagListReq),

    # 读写器写标签数据
    (API_VERSION + r'/readers/(.*)\/tagdata', ReaderProgTag),

    # 摄像头相关
    # 摄像头查询
    (API_VERSION + r'/cameras', CamerasUtils),
    (API_VERSION + r'/cameras/([^/]*)$', CameraInfoReq),
    # 摄像头拍照
    (API_VERSION + r'/cameras/(.*)\/picture', CameraCaptureReq),

    # building location
    (API_VERSION + r'/buildings', QueryLocations),
    (API_VERSION + r'/buildings/(.*)', QueryLocationInfo),
    (API_VERSION + r'/building_info/(.*)', QueryBuildingBySerial),

    # rooms
    (API_VERSION + r'/rooms', QueryRooms),
    (API_VERSION + r'/rooms/(.*)', QueryRoomInfo),

    # gateway information
    (API_VERSION + r'/gateways', QueryGateways),
    (API_VERSION + r'/gateways/(.*)', QueryGatewayInfo),

    # pos查询
    (API_VERSION + r'/pos', SmPosList),
    (API_VERSION + r'/pos/([^/]*)$', SmPosInfo),
    (API_VERSION + r'/pos/(.*)/transactions/(.*)/(.*)/(.*)', QueryPosTransInfo),

    # 门禁控制器查询
    (API_VERSION + r'/access_controller', SmAccessControllerList),
    (API_VERSION + r'/access_controller/([^/]*)$', SmAccessControllerInfo),
    (API_VERSION + r'/access_controller/(.*)/transactions/(.*)/(.*)/(.*)', QueryAccessControllerTransInfo),

    # 用户信息卡查询
    (API_VERSION + r'/idcard', SmIdCardList),
    (API_VERSION + r'/idcard/([^/]*)$', SmIdCardInfo),
    (API_VERSION + r'/idcard/(.*)/pos_transactions/(.*)/(.*)/(.*)', QueryIdcardPosTransInfo),
    (API_VERSION + r'/idcard/(.*)/access_transactions/(.*)/(.*)/(.*)', QueryIdcardAccessControllerTransInfo),

    # 传感节点查询
    (API_VERSION + r'/sensornode', SensorNodeList),
    (API_VERSION + r'/sensornode/([^/]*)$', SensorNodeInfo),

    # 传感器操作接口
    (API_VERSION + r'/sensor', SensorList),
    (API_VERSION + r'/sensor/([^/]*)$', SensorInfo),

    # 定时任务操作接口
    (API_VERSION + r'/timertask', TimerTaskList),
    (API_VERSION + r'/timertask/([^/]*)$', TimerTaskInfo),

    # 彩信接口
    (API_VERSION + r'/mms', MmsSend),
    (API_VERSION + r'/mms/(.*)', MmsStatusQuery),

    # 对外彩信接口
    (API_VERSION + r'/mmssender', MmsInterface),

    # 短信接口
    (API_VERSION + r'/sms', SmsSend),
    (API_VERSION + r'/sms/(.*)', SmsStatusQuery),

    # tags标签管理
    (API_VERSION + r'/app_data', AppDataUtils),
    (API_VERSION + r'/app_data/(.*)', AppDataOneTagUtils),

    # 触发器管理
    (API_VERSION + r'/trigger', TriggersUtils),
    (API_VERSION + r'/trigger/([^/]*)$', TriggerInfoReq),

    # 彩信测试
    #(API_VERSION + r'/mmstester', MMSTester),
]
