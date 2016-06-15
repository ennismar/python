# -*- coding: utf-8 -*-
__author__ = 'neo'

import logging

# 本进程id，每个进程openapi server唯一id
MY_ID = 1

# API版本
API_VERSION = r'/v1'

# 处理机进程配置文件，用于建立zmq连接
IOT_SERV_ZMQ_CFG = r'common/proc.json'

#zmq bind pull from the intf
PROXY_ZMQ_THREAD_NAME = 'stream_proxy-worker'
INTF_ZMQ_CONN_STR = 'tcp://0.0.0.0:6201'
PROXY_SELF_NODE_ID = 139

#zmq connect pull from the streamer
STREAMER_ZMQ_PULL_NAME = "streamer_pull-worker"
STREAMER_ZMQ_PULL_STR = "tcp://192.168.1.201:6200"

# memecache config
MEMCACHE_HOST = {("192.168.1.200:30000",1),("192.168.1.200:31000",2),("192.168.1.200:32000",3)}


# 日志级别
openapi_log_level = logging.DEBUG
