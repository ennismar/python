# -*- coding: utf-8 -*-
__author__ = 'neo'

import tornado.web
from common.call_log import update_call_log
from common.iot_msg import TAG_IOT_H_TRANSID
from common.settings import CONN_TIME_OUT
from common.auth_utils import http_basic_auth
from tornado.ioloop import IOLoop
from datetime import timedelta
import logging
import memcache
from common.settings import MEMCACHE_HOST


@http_basic_auth
class IotRequestHandler(tornado.web.RequestHandler):
    def __init__(self, application, request, **kwargs):
        super(IotRequestHandler, self).__init__(application, request, **kwargs)
        self._linkid = id(self)
        timeout_delta = timedelta(seconds=CONN_TIME_OUT)
        self.timeout_timer = IOLoop.current().add_timeout(timeout_delta, self.timeout_handler)
        if self.timeout_timer is None:
            logging.error("link[%d] add timeout timer failed" % self._linkid)

    def data_received(self, chunk):
        pass

    def write(self, chunk):
        # 记录日志
        update_call_log(self.get_status(), self.request.headers.get(TAG_IOT_H_TRANSID), chunk)
        super(IotRequestHandler, self).write(chunk)

    def get_linkid(self):
        return self._linkid

    def timeout_handler(self):
        self.timeout_timer = None
        self.set_status(408)
        self.write({"status": 1000, "status_text": "request timeout"})
        self.finish()

    def on_finish(self):
        if self.timeout_timer is not None:
            IOLoop.current().remove_timeout(self.timeout_timer)

    @staticmethod
    def get_conn_time_out():
        # 读取连接超时参数
        global CONN_TIME_OUT
        mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)
        result = mem_handle.get("conn_time_out")
        if result is not None:
            try:
                result = int(result)
                CONN_TIME_OUT = result
                
            except Exception as err_info:
                logging.error("connect time out not int[%s]" % result)

        logging.info("The connection time out %s" % CONN_TIME_OUT)
