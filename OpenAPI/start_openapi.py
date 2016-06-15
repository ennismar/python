#!/usr/bin/python3

# -*- coding: utf-8 -*-
__author__ = 'neo'

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.dirname(BASE_DIR))

# 装载支持zmq的ioloop
from zmq.eventloop import ioloop

ioloop.install()
from common.mongo_utils import *

import OpenAPI_server.api_serv as api_serv
import OpenAPI_server.serv_zmq_cfg as api_serv_zmq

import logging
import logging.handlers

import multiprocessing
from api_qos.start_api_qos import start_open_api_qos

from common.auth_utils import set_is_check_auth

from common.settings import openapi_log_level
import tornado
from tornado.options import define, options
from common.iot_request_handler import IotRequestHandler

define("checkauth", default=True, help='is check http basic Authentication', type=bool)


def init_logging():
    """
    日志文件设置，同时打印在日志文件和屏幕上
    """
    logger = logging.getLogger()
    logger.setLevel(openapi_log_level)

    sh = logging.StreamHandler()
    file_log = logging.handlers.TimedRotatingFileHandler('open_api.log', 'MIDNIGHT', 1, 0)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-7s] [%(module)s:%(filename)s-%(funcName)s-%(lineno)d] %(message)s')
    sh.setFormatter(formatter)
    file_log.setFormatter(formatter)

    # logger.addHandler(sh)
    logger.addHandler(file_log)

    logging.info("Current log level is : %s", logging.getLevelName(logger.getEffectiveLevel()))


def check_python_version():
    if sys.version[:1] != '3':
        return False
    else:
        return True


def start_open_api_server():
    """
    服务端初始化
    :return:
    """
    try:
        # 解析参数
        tornado.options.parse_command_line()

        # 设置参数
        set_is_check_auth(options.checkauth)

        # 日志初始化
        init_logging()

        # 服务端初始化
        api_serv_zmq.init_iot_serv_zmq()
        api_serv.init_api_server()

        # 打印mongo client
        logging.info(mongo_cli)

        # 读取连接超时参数
        IotRequestHandler.get_conn_time_out()

        # 启动event loop
        ioloop.IOLoop.instance().start()
    except Exception as err:
        log_str = 'OpenAPI server start fail! err = %s' % err
        logging.fatal(log_str)
        print(log_str)


def start_open_api_process():
    """
    创建OpenAPI所有进程
    :return:
    """
    try:
        process_pool = []

        # OpenAPI服务端进程
        process = multiprocessing.Process(target=start_open_api_server)
        process.start()
        process_pool.append(process)

        # OpenAPI流量控制进程
        process = multiprocessing.Process(target=start_open_api_qos)
        process.start()
        process_pool.append(process)

        for p in process_pool:
            p.join()

    except Exception as err:
        logging.fatal('start_open_api error: %s', err)


if __name__ == "__main__":
    # 检查python版本
    if check_python_version() is False:
        print('Please use python3 run the program')
        exit()

    # 启动OpenAPI
    start_open_api_process()
