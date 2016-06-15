#coding:utf-8
__author__ = 'Ennis'
from common.iot_msg import *
from common.eventno import *
from common.thread_name import *

from memcachemod.memcache_opt import set_value_to_memcache, get_value_from_memcache, delete_value_from_memcache
import logging

def handle_recv_msg(msghead, msg, stream_procs):
    try:
        eventno = msghead[TAG_RZ_H_EVENTNO]

        if eventno == IOT_PF_TO_TCPINTF_RSP or eventno == IOT_PF_TO_HTTPINTF_RSP:
            logging.info("in the evntno IOT_PF_TO_TCPINTF_RSP or  IOT_PF_TO_HTTPINTF_RSP =%d", eventno)
            pf_to_intf_rspandreq(msghead, msg, stream_procs)
        elif eventno == IOT_TCPINTF_TO_PF_REQ or eventno == IOT_HTTPINTF_TO_PF_REQ or eventno == IOT_SOCK_TCPINTF_TO_PF:
            logging.info("in the evntno IOT_TCPINTF_TO_PF_REQ or  IOT_HTTPINTF_TO_PF_REQ =%d", eventno)
            intf_to_pf_req(msghead, msg, stream_procs)
        else:
            logging.error("Get other EVENT NUMBER =%d", eventno)
    except Exception as e:
        logging.error("msg handle fail =%s", e)

def pf_to_intf_rspandreq(msghead, msg, stream_procs):
    """
    iot pf to intf resp and req , 如果是response根据linkid从memcache中获取出intf的名字，根据名字获取对应的zmqhandle，发送消息
    如果是request，直接判断http还是tcp发送消息
    :param stream_procs:
    :param msg:
    :param msghead:
    """
    try:
        linkid = msg[TAG_IOT_H_LINKID]

        if msghead[TAG_RZ_H_EVENTNO] == IOT_PF_TO_TCPINTF_RSP:
            key = "tcp:%d" % linkid
        else:
            key = "http:%d" % linkid
        value = get_value_from_memcache(key)
        logging.info("in the pf_to_intf_rsp,get memcache key=%s, value=%s", key, value)
        pack_and_send_msg(msghead, value, stream_procs)
        if msghead[TAG_RZ_H_DEST] != INTF_SRVINTF_MAIN:
            delete_value_from_memcache(key)
            logging.info("dest is not srvintf-main, delete the key=%s", key)
    except Exception as e:
        logging.error("error info = %s", e)

def intf_to_pf_req(msghead, msg, stream_procs):
    """
    intf to iot req , 根据transid为key，将intf进程名存入到memcache中，再发送消息
    :param stream_procs:
    :param msg:
    :param msghead:
    """
    try:
        linkid = msg[TAG_IOT_H_LINKID]
        value = msghead[TAG_RZ_H_SENDER]

        if msghead[TAG_RZ_H_EVENTNO] == IOT_TCPINTF_TO_PF_REQ or msghead[TAG_RZ_H_EVENTNO] == IOT_SOCK_TCPINTF_TO_PF:
            key = "tcp:%d" % linkid
        else:
            key = "http:%d" % linkid
        set_value_to_memcache(key, value)
        logging.info("in the intf_to_pf_req set memcache key=%s, value=%s", key, value)
        pack_and_send_msg(msghead, STREAMER_PUSH_WORKER, stream_procs)

        #来自srvintf的消息，解析出来判断是否是连接断开，如果是，删除memcache的key
        if msghead[TAG_RZ_H_SENDER] == INTF_SRVINTF_MAIN:
            comm_msg = unpack_commintf_msg(msghead[TAG_MSG])
            if comm_msg[TAG_COMMINTF_H_CONNMETHOD] == 1:
                delete_value_from_memcache(key)
                logging.info("connect close ,delete key=%s",key)
    except Exception as e:
        logging.error("error info = %s", e)

def pack_and_send_msg(msghead, dest, stream_procs):
    try:
        logging.info("send message to the dest=%s",dest)
        msg = pack_rz_msg(msghead)
        stream_procs[dest].send(msg)
    except Exception as e:
        logging.error("error info =%s", e)