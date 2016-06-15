# -*- coding: utf-8 -*-
# !/usr/bin/python3

# import sys
# import os

# BASE_DIR = os.path.dirname(os.path.dirname(__file__))
# sys.path.append(os.path.dirname(BASE_DIR))

# from zmq.eventloop import ioloop
from common.settings import log_level
# from client.zmq_utils import init_http_client_zmq
# from client.mongo_utils import init_mongodb
# from client.http_utils import init_async_client
import logging
import logging.handlers

__author__ = 'gz'

# 装载支持zmq的ioloop
# ioloop.install()


def init_logging():
    """
    日志文件设置，每天切换一个日志文件
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    sh = logging.StreamHandler()
    file_log = logging.handlers.RotatingFileHandler('http_client.log', maxBytes=10 * 1024 * 1024, backupCount=50)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)-7s] [%(module)s:%(filename)s-%(funcName)s-%(lineno)d] %(message)s')
    sh.setFormatter(formatter)
    file_log.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(file_log)

    logging.info("Current log level is : %s", logging.getLevelName(logger.getEffectiveLevel()))

#
# def check_python_version():
#     if sys.version[:1] != '3':
#         return False
#     else:
#         return True


if __name__ == "__main__":
    try:
        # 检查python版本
        # if check_python_version() is False:
        #     print('Please use python3 run the program')
        #     exit()

        # 日志初始化
        init_logging()

        # 初始化
        # init_http_client_zmq()
        # init_async_client()
        # init_mongodb()

        # 启动event loop
        # ioloop.IOLoop.instance().start()

    except Exception as e:
        pass
        # log_str = 'Http_client start fail! err = %s' % e
        # logging.fatal(log_str)
        # print(log_str)
