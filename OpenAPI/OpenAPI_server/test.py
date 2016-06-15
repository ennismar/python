# -*- coding: utf-8 -*-
__author__ = 'neo'

import json
import hashlib

import tornado.web

from OpenAPI_server.serv_zmq_cfg import stream_procs
from common.iot_msg import *



class ZeroMqTest(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        rz_header = {
            TAG_RZ_H_S_NODEID: 138,
            TAG_RZ_H_SENDER: API_ZMQ_THREAD_NAME,
            TAG_RZ_H_D_NODEID: 138,
            TAG_RZ_H_DEST: 'test_msg-mongo_test',
            TAG_RZ_H_EVENTNO: 1111,
            TAG_RZ_H_BUFLEN: 0,
            TAG_MSG: "api-server"
        }
        try:
            msg = pack_rz_msg(rz_header)
            stream_procs['test_msg'].send(msg)
            self.write('succ')
        except Exception as e:
            logging.error('Exception: %s', e)
            self.write('fail')


class TestMsg(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def post(self):
        try:
            body = self.request.body.decode()
            msg_dict = json.loads(body)
            logging.info('RECV = %s', msg_dict)

            iot_msg = pack_iot_msg(msg_dict['msg'])
            rz_header = {
                TAG_RZ_H_S_NODEID: msg_dict['s_nodeid'],
                TAG_RZ_H_SENDER: msg_dict['sender'],
                TAG_RZ_H_D_NODEID: msg_dict['d_nodeid'],
                TAG_RZ_H_DEST: msg_dict['dest'],
                TAG_RZ_H_EVENTNO: msg_dict['eventno'],
                TAG_RZ_H_BUFLEN: iot_msg.__len__(),
                TAG_MSG: iot_msg
            }
            msg = pack_rz_msg(rz_header)
            proc_name = msg_dict['dest'].split('-')[0]
            stream_procs[proc_name].send(msg)
            self.write('succ')
        except Exception as e:
            logging.error('Exception: %s', e)
            self.write('fail')


class TestNotifyMsg(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def post(self):
        try:
            body = self.request.body.decode()
            logging.info('Recv Notify Msg = %s', body)
            self.write('succ')
        except Exception as e:
            logging.error('Exception: %s', e)
            self.write('fail')


class TestAuth(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, username):
        try:
            cur_time = datetime.datetime.now().strftime('%Y%m%d%H%M%S%f')
            resp = 'Appkey = %s' % hashlib.sha1(username).hexdigest() + '\n'
            resp += 'AppSecret = %s' % hashlib.sha1(username + cur_time).hexdigest() + '\n'
            self.write(resp)
        except Exception as e:
            logging.error('Exception: %s', e)
            self.write('fail')


class TagNotify(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def post(self):
        try:
            body = self.request.body.decode()
            logging.info('Recv Handset Notify Tags = %s', body)
            self.write('succ')

            do_notify_msg(body)
        except Exception as e:
            logging.error('Exception: %s', e)
            self.write('fail')


class TestPerformance(tornado.web.RequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        self.write('ok')
