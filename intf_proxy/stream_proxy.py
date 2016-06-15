# coding: utf-8
__author__ = 'Ennis'
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
sys.path.append(os.path.dirname(BASE_DIR))
# 装载支持zmq的ioloop
from zmq.eventloop import ioloop
ioloop.install()
import zmqmod.serv_zmq_cfg as api_serv_zmq
import memcachemod.memcache_opt as mem_opt
import logging
import logging.handlers
from common.settings import openapi_log_level

def init_logging():
    """
    日志文件设置，同时打印在日志文件和屏幕上
    """
    logger = logging.getLogger()
    logger.setLevel(openapi_log_level)

    sh = logging.StreamHandler()
    #file_log = logging.handlers.TimedRotatingFileHandler('proxy.log', 'MIDNIGHT', 1, 0)
    file_log = logging.handlers.RotatingFileHandler('proxy.log', 'a', 50 * 1024 * 1024, 10)
    formatter = logging.Formatter('%(asctime)s %(levelname)-7s %(module)s:%(filename)s-%(funcName)s-%(lineno)d: %(message)s')
    sh.setFormatter(formatter)
    file_log.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(file_log)

    logging.info("Current log level is : %s", logging.getLevelName(logger.getEffectiveLevel()))

def check_python_version():
    if sys.version[:1] != '3':
        return False
    else:
        return True

if __name__ == "__main__":
    try:
        # 检查python版本
        if check_python_version() is False:
            print('Please use python3 run the program')
            exit()
        # 日志初始化
        init_logging()

        # 服务端初始化
        api_serv_zmq.init_iot_serv_zmq()

        #初始化memcache
        mem_opt.init_memcache()

        # 启动event loop
        ioloop.IOLoop.instance().start()
    except Exception as e:
        log_str = 'OpenAPI start fail! err = %s' % e
        logging.fatal(log_str)
        print(log_str)




