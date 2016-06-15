# -*- coding: utf-8 -*-
import logging.handlers
from tornado import ioloop
from common.settings import *
from api_qos.api_token_bucket import TokenBucket

__author__ = 'gz'


def init_logging():
    """
    日志文件设置
    """
    logger = logging.getLogger()
    logger.setLevel(qos_log_level)

    sh = logging.StreamHandler()
    file_log = logging.handlers.RotatingFileHandler('qos.log', maxBytes=10 * 1024 * 1024, backupCount=50)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)-7s] [%(module)s:%(filename)s-%(funcName)s-%(lineno)d] %(message)s')
    sh.setFormatter(formatter)
    file_log.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(file_log)

    logging.info("Current log level is : %s", logging.getLevelName(logger.getEffectiveLevel()))


def start_open_api_qos():
    try:

        # 日志初始化
        init_logging()

        # 使用令牌桶控制流量
        for api in QOS_API:
            if not TokenBucket(api).start():
                return

        ioloop.IOLoop.instance().start()

    except Exception as err:
        log_str = 'OpenApiQoS start fail! err = %s' % err
        logging.fatal(log_str)
