# -*- coding: utf-8 -*-
__author__ = 'neo'

# import urllib
import json

import tornado.web
import tornado.gen
import tornado.httpclient

from common.iot_msg import *


# http client pool
http_client_pool = {}


def http_resp(msg):
    """
    返回http response
    :param msg:
    """
    try:
        logging.info("Need Send Resp = %s", msg)

        if msg[TAG_IOT_H_LINKID] in http_client_pool.keys():
            if isinstance(msg[TAG_MSG], bytes):
                resp = msg[TAG_MSG].decode()
                try:
                    resp = json.loads(resp)
                except Exception:
                    resp = msg[TAG_MSG]
            else:
                resp = msg[TAG_MSG]

            http_client_pool[msg[TAG_IOT_H_LINKID]].write(resp)
            http_client_pool[msg[TAG_IOT_H_LINKID]].finish()
        else:
            logging.error("Can't find http client by linkid = %d", msg[TAG_IOT_H_LINKID])
    except Exception as e:
        logging.error("send response fail!, linkid = %d, err = %s", msg[TAG_IOT_H_LINKID], e)
        pass


@tornado.gen.engine
def http_client_post(msg, header_method, http_instance, url):
    """
    调用门户api接口完成增、删、改操作
    :param url: 门户接口url
    :param msg: dict类型http body
    :param header_method:
    :param http_instance:
    """
    header, body = {}, ""
    try:
        header = {'method': header_method}
        #header['Content-Type'] = 'application/x-www-form-urlencoded'
        if msg is not None and msg != '':
            body = json.dumps(msg)

        client = tornado.httpclient.AsyncHTTPClient()

        logging.info('call Web Api, url = %s, header = %s, body = %s', url, header, body)
        response = yield tornado.gen.Task(client.fetch, url, method='POST', headers=header, body=body)
        logging.info('url = %s, Resp = %d:%s', url, response.code, response.body)
        http_instance.set_status(response.code)
        try:
            http_instance.write(json.loads(response.body.decode()))
        except Exception:
            http_instance.write(response.body.decode())
        http_instance.finish()
    except Exception as e:
        logging.error('Call WEB API fail! url = %s, header = %s, body = %s, err = %s', url, header, body, e)
        http_instance.write({"status": 1000, "status_text": "Internal system error"})
        http_instance.set_status(500)
        http_instance.finish()


@tornado.gen.coroutine
def http_client_post_with_result(msg, header_method, http_instance, url):
    """
    使用http协议发送请求，能够返回响应数据给调用接口
    :param url: 门户接口url
    :param msg: dict类型http body
    :param header_method:
    :param http_instance:
    """
    header, body = {}, ""
    try:
        header = {'method': header_method}
        if msg is not None and msg != '':
            body = json.dumps(msg)

        client = tornado.httpclient.AsyncHTTPClient()

        logging.info('call Web Api, url = %s, header = %s, body = %s', url, header, body)
        response = yield tornado.gen.Task(client.fetch, url, method='POST', headers=header, body=body)
        # logging.info('url = %s, Resp = %d:%s', url, response.code, response.body)
        return response

    except Exception as e:
        logging.error('Call WEB API fail! url = %s, header = %s, body = %s, err = %s', url, header, body, e)
        http_instance.write({"status": 1000, "status_text": "Internal system error"})
        http_instance.set_status(500)
        http_instance.finish()


