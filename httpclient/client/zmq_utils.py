# -*- coding: utf-8 -*-

import sys
import getpass
import json

import zmq
from zmq.eventloop import zmqstream

from common.settings import HTTP_CLI_ZMQ_CONN_STR, HTTP_CLI_ZMQ_CFG
from common.iot_msg import *
from client.http_utils import http_client_post, stream_procs

__author__ = 'gz'


def set_zmq_sock_opt(socket, option, value):
    """
    设置zmq socket属性
    :param socket:
    :param option:
    :param value:
    """
    try:
        socket.setsockopt(option, value)
    except Exception as err:
        logging.error('set_zmq_sock_opt fail! sock = %s, option = %s, value = %d, err = %s', socket, option, value, err)


def set_zmq_socket_default_option(socket):
    """
    默认为每个zmq socket设置属性
    :param socket:
    """
    try:
        set_zmq_sock_opt(socket, zmq.SNDBUF, 65535)
        set_zmq_sock_opt(socket, zmq.RCVBUF, 65535)
        set_zmq_sock_opt(socket, zmq.SNDTIMEO, 100)
        set_zmq_sock_opt(socket, zmq.IMMEDIATE, 1)
    except Exception as err:
        logging.error('set_zmq_socket_default_option fail! sock = %s, err = %s', socket, err)


def init_http_client_zmq():
    """
    1、创建自己的zmq poll连接
    2、读取处理机配置文件，对每个进程创建push连接
    """

    # 创建zmq context
    context = zmq.Context()

    # 创建自己的poll连接
    socket_pull = context.socket(zmq.PULL)
    socket_pull.bind(HTTP_CLI_ZMQ_CONN_STR)

    # 设置socket属性
    set_zmq_socket_default_option(socket_pull)

    api_serv_stream_pull = zmqstream.ZMQStream(socket_pull)
    api_serv_stream_pull.on_recv(recv_msg)
    logging.info('api server PULL message on: %s', HTTP_CLI_ZMQ_CONN_STR)

    # 创建与处理机的连接
    try:
        with open(HTTP_CLI_ZMQ_CFG) as config__file:
            proc_json = json.load(config__file)
            logging.info('proc = %s', proc_json)

            for one_proc in proc_json:
                proc_port = one_proc.get('port', '0')
                proc_ip = one_proc.get('ip', '0.0.0.0')
                proc_name = one_proc.get('proc_name', None)
                if proc_name is None:
                    logging.error('invalid config = %s', one_proc)
                    continue
                elif proc_name == HTTP_CLI_THREAD_NAME:
                    # 配置进程名与自身相同，无需建立连接
                    continue
                else:
                    if sys.platform == 'win32':
                        if int(proc_port) == 0:
                            logging.error("ipc mode can't work on windows!, proc = %s", proc_name)
                            continue
                        else:
                            conn_str = "tcp://%s:%s" % (proc_ip, proc_port)
                    else:
                        if int(proc_port) == 0:
                            conn_str = "ipc:///dev/shm/%s_%s.ipc" % (getpass.getuser(), proc_name)
                        else:
                            conn_str = "tcp://%s:%s" % (proc_ip, proc_port)

                    socket_push = context.socket(zmq.PUSH)
                    socket_push.connect(conn_str)

                    # 设置socket属性
                    set_zmq_socket_default_option(socket_push)

                    stream_push = zmqstream.ZMQStream(socket_push)
                    stream_procs[proc_name] = stream_push
                    logging.info('api server PUSH message to: %s - %s', proc_name, conn_str)
    except Exception as err:
        logging.error('zmq init error! err = %s', err)


def recv_msg(msgs):
    """
    zmq收到消息的入口函数，可能一次性收到多条，msgs是一个list，逐条处理
    :param msgs: 本次收到的消息list
    :return:
    """
    for one_msg in msgs:
        try:
            # 解析os 头
            parsed_msg = unpack_rz_msg(one_msg)
            logging.info('parsed_msg = %s', parsed_msg)

            if parsed_msg[TAG_RZ_H_EVENTNO] != IOT_NOTIFY_TO_CLIENT:
                logging.error('RZ_header event_no error!')
                continue

            # 解析iot 头
            iot_msg = unpack_iot_msg(parsed_msg[TAG_MSG])
            logging.info('iot_msg = %s', iot_msg)

            if iot_msg == {}:
                logging.error('unpack msg fail!')
                continue

        except Exception as err:
            logging.error('Parse msg fail! e = %s', err)
            return

        trans_id = iot_msg.get(TAG_IOT_H_TRANSID, None)
        logging.info('trans_id: [%s]', trans_id)

        try:
            msg = json.loads(iot_msg[TAG_MSG].decode())
        except Exception as err:
            logging.error('msg loads error! e = %s', err)
            return

        msg_body = msg.get(TAG_BODY, None)
        if msg_body is not None:
            try:
                post_body = json.dumps(msg_body)
            except Exception as err:
                logging.error('msg dumps error! e = %s', err)
                return
        else:
            post_body = None

        try:
            # 向第三方发送消息
            sender = parsed_msg[TAG_RZ_H_SENDER]
            app_key = msg[TAG_APP_KEY]
            cb_url = msg[TAG_URL]
            http_client_post(iot_msg, sender, app_key, cb_url, post_body)
        except Exception as err:
            logging.error('http_client_post fail! e = %s', err)
            return
