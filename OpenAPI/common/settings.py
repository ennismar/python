# -*- coding: utf-8 -*-
__author__ = 'neo'

import logging

IS_DEBUG = 1

# API版本
API_VERSION = r'/v1'

# API接口服务端口
HTTP_SERVER_PORT = 7000

# 处理机进程配置文件，用于建立zmq连接
IOT_SERV_ZMQ_CFG = r'common/proc.json'

# SERVER zmq pull连接
API_ZMQ_THREAD_NAME = 'api-worker'
API_ZMQ_CONN_STR = 'tcp://0.0.0.0:7778'
API_SELF_NODE_ID = 138

# CLIENT zmq pull连接
CLI_ZMQ_THREAD_NAME = 'api_cli-worker'
CLI_ZMQ_CONN_STR = 'tcp://0.0.0.0:9998'
CLI_SELF_NODE_ID = 138

STORAGE_DIR = "/home/iot"

# mongo配置
MONGO_HOST = ["/ITTILNOQvCjUy3Rb1Whe7vLKRMHuaRlR3sqImkC+xGZtemo6WgE1sgxplC0B3UR"]
MONGO_HOST_DEBUG = ["mongodb://iot:iot@192.168.1.200:20000/iot"]

DECODE_LIB = "librz.so"

# memcache配置
MEMCACHE_HOST = ["192.168.1.200:30000"]

# 门户api url
PORTAL_API_URL = "http://192.168.1.200:7070/internalService/"

# OpenAPI服务端进程日志级别
openapi_log_level = logging.DEBUG

MMS_HANDLE_TIME = 3000  # ms
MMS_LOCK_CHECK_INTERVAL = 100  # ms

# 流量控制进程相关设置
# 流量控制日志级别
qos_log_level = logging.INFO
# 流量控制api
#QOS_API = ['sms', 'mms']
QOS_API = ['mms']
# 令牌增加定时(s)
TOKEN_TIMER = 0.1
# 分布式锁默认过期时间(s)
DISTRIBUTE_LOCK_TIME = 3

# 连接默认超时超时时间(s)
CONN_TIME_OUT = 3
