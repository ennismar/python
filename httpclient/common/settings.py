# -*- coding: utf-8 -*-

import logging

__author__ = 'gz'


# 处理机进程配置文件，用于建立zmq连接
HTTP_CLI_ZMQ_CFG = r'common/proc.json'


# http client zmq pull连接
HTTP_CLI_THREAD_NAME = 'http_client'
HTTP_CLI_ZMQ_CONN_STR = 'tcp://0.0.0.0:5015'
HTTP_CLI_SELF_NODE_ID = 138

# mongodb配置
MONGODB_HOST = "/ITTILNOQvCjUy3Rb1Whe7vLKRMHuaRlR3sqImkC+xGZtemo6WgE1sgxplC0B3UR"
MONGODB_HOST_DEBUG = "mongodb://iot:iot@192.168.1.200:20000/iot"

DECODE_LIB = "librz.so"

# 日志级别
log_level = logging.DEBUG

# 请求超时时间(s)
REQUEST_TIME_OUT = 5
