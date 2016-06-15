# -*- coding: utf-8 -*-
__author__ = 'neo'

import datetime
from common.mongo_utils import *
from common.iot_msg import TAG_IOT_H_TRANSID


def insert_call_log(appkey, requesthandler):
    """
    收到openapi请求后，生成日志记录
    :param appkey:
    :param requesthandler:
    """
    try:
        # 获取request请求中的相关信息
        call_info = {
            'method': requesthandler.request.method,
            'url': requesthandler.request.uri
        }
        invoke_ip = requesthandler.request.remote_ip
        current_time = datetime.datetime.utcnow()
        transid = requesthandler.request.headers.get(TAG_IOT_H_TRANSID, '')
        if transid == '':
            logging.error('Trans id is NULL')
            return

        call_log = {
            'appkey': appkey,
            'transid': transid,
            'call_info': call_info,
            'recvtime': current_time,
            'invoke_ip': invoke_ip,
            'status': 1000 # 初始记录，status默认为失败
        }

        logging.debug('insert call log: %s', call_log)
        try:
            mongo_cli[DB_IOT]['openapi_calllog'].insert(call_log)
        except Exception as err:
            logging.error('mongo_insert Exception, err = %s', err)
    except Exception as err:
        logging.error('Exception, err = %s', err)


def update_call_log(http_status, transid, response):
    """
    收到响应后，更新日志信息
    :param http_status:
    :param transid:
    :param response:
    """
    try:
        is_dict = isinstance(response, dict)
        # logging.debug('update call log, transid = %s, response = %s, response is dict = %s', transid, response, is_dict)

        current_time = datetime.datetime.now().utcnow()

        # 如果客户端调用了不支持的方法，返回的是一个html string
        if is_dict:
            # 解析response报文
            # 对于报文里有status和statustext字段的，按报文字段填写日志
            # 对于查询请求，没有status字段的，都是查询成功
            if http_status == 200:
                status = 0
                status_text = response.get('status_text', '')

                # 门户接口返回msg描述
                if status_text == '':
                    status_text = response.get('msg', '')
            else:
                status = 1000
                status_text = response.get('status_text', '')
                # 门户接口返回msg描述
                if status_text == '':
                    status_text = response.get('msg', '')
        else:
            if http_status != 200:
                status = 1000
                status_text = 'fail'
            else:
                status = 0
                status_text = 'success'

        call_log = {
            'resptime': current_time,
            'status': status,
            'statustext': status_text
        }

        logging.debug('update call log: %s', call_log)
        mongo_cli[DB_IOT]['openapi_calllog'].update({'transid': transid}, {'$set':call_log}, multi=True)
    except Exception as err:
        logging.error('mongo_update Exception, err = %s', err)
