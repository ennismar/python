# -*- coding: utf-8 -*-

import logging
import tornado.gen
import sys
from motor.motor_tornado import MotorClient
from common.settings import MONGODB_HOST, MONGODB_HOST_DEBUG
from common.decryption import decrypt

__author__ = 'gz'

DB_IOT = 'iot'
COL_CALL_LOG = 'openapi_calllog'

TAG_TRANS_ID = 'transid'
TAG_REQUEST_ID = 'request_id'
TAG_APP_KEY = 'appkey'
TAG_SENDER = 'sender'
TAG_STATUS = 'status'
TAG_STATUS_TEXT = 'statustext'
TAG_RCV_TIME = 'recvtime'
TAG_RSP_TIME = 'resptime'
TAG_RSP_DATA = 'rspdata'

mongodb_cli = None


def init_mongodb():
    """
    建立mongodb连接
    :return:
    """
    if sys.platform == 'linux':
        mongodb_uri = decrypt(MONGODB_HOST)
    else:
        mongodb_uri = MONGODB_HOST_DEBUG

    global mongodb_cli
    try:
        mongodb_cli = MotorClient(mongodb_uri)
        logging.info("init mongodb, %s", mongodb_cli)
    except Exception as err:
        logging.error("Can't connect to mongodb! %s", err)


@tornado.gen.coroutine
def insert_call_log(doc):
    """
    添加open api调用日志记录
    :param doc: 插入内容dict
    :return:
    """
    try:
        request_id = doc.get(TAG_REQUEST_ID, None)
        logging.info('insert call log[%s]', request_id)
        global mongodb_cli
        future = yield mongodb_cli[DB_IOT][COL_CALL_LOG].insert(doc)
        logging.info('insert call log[%s] success, result: [%s]', request_id, repr(future))
    except Exception as err:
        logging.error('insert call log fail, error: [%s]', err)
