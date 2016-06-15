# -*- coding: utf-8 -*-
__author__ = 'neo'


# 查询条件标签定义
Q_OFFSET = "offset"
Q_LIMIT = "limit"
Q_TOTAL = "total"

TAG_META_DATA = "meta_data"

TAG_COMPANYS = "companys"
TAG_COMPANY_CODE = "company_code"

TAG_TERM_CODE = "term_code"

TAG_READERS = "readers"
TAG_READER_CODE = "reader_code"
TAG_READER_NAME = "reader_name"
TAG_READER_TYPE = "reader_type"

TAG_CAMERAS = "cameras"
TAG_CAMERA_NAME = "camera_name"
TAG_CAMERA_CODE = "camera_code"


TAG_NAME = "name"
TAG_TYPE = "type"
TAG_DESC = "desc"
TAG_MODELS = "models"
TAG_SERVER_INFO = "server_info"

TAG_PARAMS = "params"
TAG_COMMANDS = "cmds"

TAG_BUILDINGS = "buildings"
TAG_BUILDING_NAME = "building_name"
TAG_COORDINATE = "coordinate"
TAG_LATITUDE = "latitude"
TAG_LONGITUDE = "longitude"
TAG_DISTANCE = "distance"
TAG_BUILDING_CODE = "building_code"
TAG_DETAIL_INFO = "detail_info"
TAG_SERIAL = "serial"

TAG_ROOMS = "rooms"
TAG_ROOM_CODE = "room_code"
TAG_ROOM_DESC = "room_desc"
TAG_ROOM_COORDINATE = "room_coordinate"


# 写标签命令
PROGRAM_EPC = "ProgramEPC".lower()
PROGRAM_USER_DATA = "ProgramUser".lower()

# api_user
TAG_APPKEY = "appkey"
TAG_APPID = "app_id"
TAG_APPSECRET = "appsecret"
TAG_TOKEN = "token"
TAG_USER_API = "available_apis"

# gateway
TAG_GATEWAYS = "gateways"
TAG_GATEWAY_NAME = "gate_name"
TAG_GATEWAY_TYPE = "gate_type"
TAG_GATEWAY_CODE = "gate_code"

# dictionary 表
TAG_DICT_TYPE = 'dictype'
TAG_DICT_VALUE = 'dicvalue'

TAG_MAC_ADDR = "mac_addr"

TAG_STATUS = "status"
TAG_CONNECTION = "connection"
TAG_MSGTYPE = "msgtype"

# 一卡通资源
TAG_UNIQUEID = "uniqueid"
TAG_PRODUCT_NUM = "productnumber"
TAG_IDCARD_NO = "currentasn"
TAG_POS_CODE = "pos_code"
TAG_ACCESS_CONTROLLER_CODE = "access_controller_code"
TAG_IDCARD_CODE = "idcard_code"
TAG_SENSORNODE_CODE = "node_code"
TAG_SENSOR_CODE = "sensor_code"
TAG_TIMERTASK_CODE = "task_code"
TAG_POS = "pos"
TAG_ACCESS_CONTROLLER = "access_controller"
TAG_IDCARD = "idcard"
TAG_SENSORNODE = "sensornode"
TAG_SENSOR = "sensor"
TAG_TIMERTASK = "timertask"


# 开始、结束时间标签
TAG_START_TIME = 'start_time'
TAG_END_TIME = 'end_time'

# term op表req标签
TAG_TERM_OP_REQ = 'req'
TAG_TERM_OP_OPTIME = 'optime'
TAG_TERM_OP_DEVICE_CODE = 'device_code'
TAG_TERM_OP_REQTYPE = 'reqtype'

# 交易记录tag
TAG_TRANSACTIONS = 'trans'
TAG_SORT_FLAG = 'sort'

# app data
TAG_DATA_CODE = 'data_code'
TAG_DATA_INFO = 'data'

TAG_QUERY_CONDITIONS = 'conditions'
TAG_QUERY_RESULT_TAG_LIST = 'result_tag_list'

# triggers
TAG_TRIGGERS = 'triggers'
TAG_TRIGGER_CODE = 'trigger_code'
TAG_TRIGGER_NAME = 'name'
TAG_TRIGGER_SRC_DEVCODE = 'src_device_code'
TAG_TRIGGER_SRC_TYPE = 'src_type'
TAG_TRIGGER_SRC_REQTYPE = 'src_reqtype'
TAG_TRIGGER_DST_DEVCODE = 'dst_device_code'
TAG_TRIGGER_DST_TYPE = 'dst_type'
TAG_TRIGGER_DST_REQTYPE = 'dst_reqtype'

# 传感器
TAG_OWN_CODE = "own_code"

TAG_SMS_TEMPLATE = "template"
