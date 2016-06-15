# -*- coding: utf-8 -*-

__author__ = 'neo'

import sys
import getpass
import json

import zmq
from zmq.eventloop import zmqstream

from common.settings import API_ZMQ_CONN_STR, IOT_SERV_ZMQ_CFG
from common.iot_msg import *
from OpenAPI_server.http_utils import http_resp


# 各处理机进程push消息句柄
stream_procs = {}


def set_zmq_sock_opt(socket, option, value):
    """
    设置zmq socket属性
    :param socket:
    :param option:
    :param value:
    """
    try:
        socket.setsockopt(option, value)
    except Exception as e:
        logging.error('set_zmq_sock_opt fail! sock = %s, option = %s, value = %d, err = %s', socket, option, value, e)


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
    except Exception as e:
        logging.error('set_zmq_socket_default_option fail! sock = %s, err = %s', socket, e)


def init_iot_serv_zmq():
    """
    1、创建自己的zmq poll连接
    2、读取处理机配置文件，对每个进程创建push连接
    """

    # 创建zmq context
    context = zmq.Context()

    # 创建自己的poll连接
    socket_pull = context.socket(zmq.PULL)
    socket_pull.bind(API_ZMQ_CONN_STR)

    # 设置socket属性
    set_zmq_socket_default_option(socket_pull)

    api_serv_stream_pull = zmqstream.ZMQStream(socket_pull)
    api_serv_stream_pull.on_recv(recv_msg)
    logging.info('api server PULL message on: %s', API_ZMQ_CONN_STR)

    # 创建与iot server的连接
    try:
        with open(IOT_SERV_ZMQ_CFG) as config__file:
            proc_json = json.load(config__file)
            logging.info('proc = %s', proc_json)

            for one_proc in proc_json:
                proc_port = one_proc.get('port', '0')
                proc_ip = one_proc.get('ip', '0.0.0.0')
                proc_name = one_proc.get('proc_name', None)
                if proc_name is None:
                    logging.error('invalid config = %s', one_proc)
                    continue
                elif proc_name == API_ZMQ_THREAD_NAME:
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
    except Exception as e:
        logging.error('zmq init error! err = %s', e)


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

            # 解析iot 头
            iot_msg = unpack_iot_msg(parsed_msg[TAG_MSG])
            logging.info('iot_msg = %s', iot_msg)

            if iot_msg == {}:
                logging.error('unpack msg fail!')
                continue

            http_resp(iot_msg)
        except Exception as e:
            logging.error('Parse msg fail! e = %s', e)
            return
