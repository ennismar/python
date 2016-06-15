# -*- coding: utf-8 -*-
__author__ = 'neo'

import logging

import tornado.httpserver
import tornado.web

from OpenAPI_server.urls import app_handlers
from common.settings import HTTP_SERVER_PORT


def init_api_server():
    """
    初始化设置http server的参数
    :return:
    """
    try:
        # 装载url配置
        app = tornado.web.Application(
            handlers=app_handlers
        )

        # 配置server
        api_server = tornado.httpserver.HTTPServer(app)
        api_server.listen(HTTP_SERVER_PORT)
        logging.info("start http server at: %d", HTTP_SERVER_PORT)
    except Exception as e:
        logging.error('Exception: %s', e)
