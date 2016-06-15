# -*- coding: utf-8 -*-

from tornado.httpclient import HTTPRequest, HTTPError
from client.mongo_utils import *
from common.iot_msg import *
from common.settings import REQUEST_TIME_OUT
import tornado.gen
import logging
import json
import datetime

__author__ = 'gz'

# http client pool
http_client_pool = {}

# 各处理机进程push消息句柄
stream_procs = {}

http_cli = None


def send_msg_to_iot(dst_name, msg):
    """
    发送消息到目的进程
    :param dst_name: 目的进程名
    :param msg: 完整消息内容
    :return:
    """
    if dst_name in stream_procs.keys():
        stream_procs[dst_name].send(msg)
        logging.info('Send resp success! process = %s', dst_name)
        return True
    else:
        logging.error("Can't find process = %s", dst_name)
        return False


def resp_msg(iot_msg, dst_name, status, status_text, context):
    """
    向处理机发送反馈消息
    :param iot_msg:
    :param dst_name: 目的进程名
    :param status: 成功失败状态 0成功，其它失败
    :param status_text: 结果描述
    :param context: 反馈内容
    :return:
    """
    try:
        trans_id = iot_msg[TAG_IOT_H_TRANSID]
        logging.debug('resp_msg trans_id[%s]', trans_id)

        resp_dict = {
            TAG_STATUS: status,
            TAG_STATUS_TEXT: status_text,
        }

        if context is not None:
            try:
                resp_dict[TAG_CONTEXT] = json.loads(context)
            except Exception:
                resp_dict[TAG_CONTEXT] = context

        resp_body = json.dumps(resp_dict)

        ret, msg = pack_iot_rsp(iot_msg, resp_body, dst_name)
        if ret is True:
            # 发送消息给处理机
            if send_msg_to_iot(dst_name, msg) is True:
                logging.info('Send response success! trans_id[%s], msg[%s]', trans_id, resp_body)
            else:
                logging.error('Send response failed! trans_id[%s], msg[%s]', trans_id, resp_body)

    except Exception as err:
        logging.error('Send rsp fail! err = %s', err)


def init_async_client():
    """
    初始化异步client
    :return:
    """
    try:
        global http_cli
        http_cli = tornado.httpclient.AsyncHTTPClient()
        logging.info('init AsyncHTTPClient success')
    except Exception as err:
        logging.error('init AsyncHTTPClient fail, err: [%s]', err)


@tornado.gen.engine
def http_client_post(iot_msg, sender, app_key, url, body):
    """
    异步post消息到应用url
    :param iot_msg: iot消息内容
    :param sender: 平台发送消息进程名
    :param app_key: 应用编码
    :param url: 应用通知url地址
    :param body: 通知具体内容
    :return:
    """
    try:
        trans_id = iot_msg[TAG_IOT_H_TRANSID]
        logging.info('http client post, trans_id: [%s], url: [%s], body: [%s]', trans_id, url, body)

        rcv_time = datetime.datetime.now()

        # 设置超时为5s
        request_id = "REQ" + str(HTTP_CLI_SELF_NODE_ID) + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
        header = {"Content-Type": "text/plain"}
        request = HTTPRequest(url=url, method="POST", headers=header, body=body, request_timeout=REQUEST_TIME_OUT)

        # 异步发送post请求，等待响应
        logging.info("post msg, trans_id = [%s], request_id = [%s]", trans_id, request_id)

        global http_cli
        response = yield tornado.gen.Task(http_cli.fetch, request)
        logging.info('request_id = [%s], response code: [%d]', request_id, response.code)

        # 反馈处理
        http_response_handle(request_id, iot_msg, sender, app_key, rcv_time, response)

    except Exception as err:
        logging.error('callback app fail! url = %s, body = %s, err = %s', url, body, err)


def http_response_handle(request_id, iot_msg, sender, app_key, rcv_time, response):
    """
    http请求反馈处理
    :param request_id: http请求唯一id
    :param iot_msg: 平台trans_id
    :param sender: 平台发送消息进程名
    :param app_key: 平台发送消息应用
    :param rcv_time: 平台发送消息时间
    :param response: HTTP Response object.
    :return:
    """
    try:
        if response.code == 200:
            status = 0
            status_text = response.reason
        else:
            status = response.code
            if type(response.error) is HTTPError:
                status_text = response.reason
            else:
                status_text = repr(response.error)

        logging.info('request_id: [%s], sender: [%s], status: [%d:%s]', request_id, sender, status, status_text)

        # insert内容
        document = {
            TAG_REQUEST_ID: request_id,
            TAG_TRANS_ID: iot_msg[TAG_IOT_H_TRANSID],
            TAG_APP_KEY: app_key,
            TAG_SENDER: sender,
            TAG_STATUS: status,
            TAG_STATUS_TEXT: status_text,
            TAG_RCV_TIME: rcv_time,
            TAG_RSP_TIME: datetime.datetime.now(),
        }

        rsp_data = None
        if status == 0 and type(response.body) is bytes:
            rsp_data = response.body.decode()
            document[TAG_RSP_DATA] = rsp_data

        # 添加日志
        insert_call_log(document)

        # 向处理机发送反馈消息
        resp_msg(iot_msg, sender, status, status_text, rsp_data)

    except Exception as err:
        logging.error('http_response_handle fail! err = %s', err)
