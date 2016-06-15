# -*- coding: utf-8 -*-
__author__ = 'neo'

import struct
import logging
import time

from common.settings import API_ZMQ_THREAD_NAME, API_SELF_NODE_ID




# T_OS_MSG_HEAD的struct format定义
RZ_HEADER_STRUCT_FMT = '=i33si33sHH'
RZ_HEADER_LEN = struct.calcsize(RZ_HEADER_STRUCT_FMT)

# T_IOT_MSG的struct format定义
IOT_HEADER_STRUCT_FMT = '=Q33s33s33s33sH'
IOT_HEADER_LEN = struct.calcsize(IOT_HEADER_STRUCT_FMT)

# header dict中tag定义
TAG_RZ_H_S_NODEID = 's_nodeid'
TAG_RZ_H_SENDER = 'sender'
TAG_RZ_H_D_NODEID = 'd_nodeid'
TAG_RZ_H_DEST = 'dest'
TAG_RZ_H_EVENTNO = 'eventno'
TAG_RZ_H_BUFLEN = 'buflen'

TAG_IOT_H_LINKID = 'linkid'
TAG_IOT_H_TRANSID = 'transid'
TAG_IOT_H_MSGTYPE = 'msgtype'
TAG_IOT_H_TERM_CODE = 'term_code'
TAG_IOT_H_DEVICE_CODE = 'device_code'
TAG_IOT_H_MSGLEN = 'msglen'

# 消息体tag
TAG_MSG = 'msg'


def fix_str(src_string):
    """
    对于字符串，去掉\00部分
    :param src_string:
    :return:
    """
    if src_string is not None:
        idx = src_string.find('\x00')
        if idx > 0:
            src_string = src_string[:idx]

    return src_string


def pack_rz_msg(rz_header):
    """
    组装rz消息头结构
    :param rz_header: 字典类型
    :return:
    """
    if rz_header is None:
        logging.fatal('param is None!')
        return ""

    try:
        if int(rz_header[TAG_RZ_H_BUFLEN]) <= 0:
            rz_header[TAG_RZ_H_BUFLEN] = len(rz_header[TAG_MSG])

        fmt = RZ_HEADER_STRUCT_FMT + str(rz_header[TAG_RZ_H_BUFLEN]) + 's'

        packed_msg = struct.pack(fmt, rz_header[TAG_RZ_H_S_NODEID], rz_header[TAG_RZ_H_SENDER].encode(), rz_header[TAG_RZ_H_D_NODEID],
                                 rz_header[TAG_RZ_H_DEST].encode(), rz_header[TAG_RZ_H_EVENTNO], rz_header[TAG_RZ_H_BUFLEN], rz_header[TAG_MSG])
    except Exception as e:
        logging.error('pack_rz_msg Exception: %s', e)
        packed_msg = ""

    return packed_msg


def unpack_rz_msg(packed_msg):
    """
    解析rz消息头结构
    :param packed_msg:
    :return:
    """
    if packed_msg is None:
        logging.fatal('param is None!')
        return {}

    try:
        # 先解析消息头，获取消息具体长度
        rz_header = struct.unpack(RZ_HEADER_STRUCT_FMT, packed_msg[:RZ_HEADER_LEN])
        logging.debug('RZ_header = %s', rz_header)

        # 从header中获取buflen，重组fmt，再次解析msg，获取具体消息体内容
        buf_len = str(rz_header[len(rz_header) - 1])
        fmt = RZ_HEADER_STRUCT_FMT + buf_len + 's'
        tmp = struct.unpack(fmt, packed_msg)
        logging.info("RECV = %s", tmp)

        unpacked_msg = {
            TAG_RZ_H_S_NODEID: int(tmp[0]),
            TAG_RZ_H_SENDER: fix_str(tmp[1].decode()),
            TAG_RZ_H_D_NODEID: int(tmp[2]),
            TAG_RZ_H_DEST: fix_str(tmp[3].decode()),
            TAG_RZ_H_EVENTNO: tmp[4],
            TAG_RZ_H_BUFLEN: tmp[5],
            TAG_MSG: tmp[6]
        }
    except Exception as e:
        logging.error('unpack_rz_msg fail! err = %s', e)
        unpacked_msg = {}

    return unpacked_msg


def pack_iot_msg(iot_header):
    """
    组装iot消息头结构
    :param iot_header: 字典类型
    :return:
    """
    if iot_header is None:
        logging.fatal('param is None!')
        return ""

    try:
        if int(iot_header[TAG_IOT_H_MSGLEN]) <= 0:
            iot_header[TAG_IOT_H_MSGLEN] = len(iot_header[TAG_MSG])

        fmt = IOT_HEADER_STRUCT_FMT + str(iot_header[TAG_IOT_H_MSGLEN]) + 's'

        packed_msg = struct.pack(fmt, iot_header[TAG_IOT_H_LINKID], iot_header[TAG_IOT_H_TRANSID].encode(), iot_header[TAG_IOT_H_MSGTYPE].encode(),
                                 iot_header[TAG_IOT_H_TERM_CODE].encode(), iot_header[TAG_IOT_H_DEVICE_CODE].encode(), iot_header[TAG_IOT_H_MSGLEN], iot_header[TAG_MSG].encode())
    except Exception as e:
        logging.error('pack_iot_msg Exception: %s', e)
        packed_msg = ""

    return packed_msg


def unpack_iot_msg(packed_msg):
    """
    解析iot消息头结构
    :param packed_msg:
    :return:
    """
    if packed_msg is None:
        logging.fatal('param is None!')
        return {}

    try:
        # 先解析消息头，获取消息具体长度
        iot_header = struct.unpack(IOT_HEADER_STRUCT_FMT, packed_msg[:IOT_HEADER_LEN])
        logging.debug('IOT_header = %s', iot_header)

        # 从header中获取buflen，重组fmt，再次解析msg，获取具体消息体内容
        msglen = str(iot_header[len(iot_header) - 1])
        fmt = IOT_HEADER_STRUCT_FMT + msglen + 's'
        tmp = struct.unpack(fmt, packed_msg)
        logging.info("RECV = %s", tmp)

        unpacked_msg = {
            TAG_IOT_H_LINKID: int(tmp[0]),
            TAG_IOT_H_TRANSID: fix_str(tmp[1].decode()),
            TAG_IOT_H_MSGTYPE: fix_str(tmp[2].decode()),
            TAG_IOT_H_TERM_CODE: fix_str(tmp[3].decode()),
            TAG_IOT_H_DEVICE_CODE: fix_str(tmp[4].decode()),
            TAG_IOT_H_MSGLEN: int(tmp[5]),
            TAG_MSG: tmp[6]
        }
    except Exception as e:
        logging.error('unpack_iot_msg fail! source_msg_len = %d, err = %s', len(packed_msg), e)
        unpacked_msg = {}

    return unpacked_msg


def get_timestamp():
    """
    生成timestamp
    """
    current_time = time.time()
    return ((int(current_time) % 86400) * 1000) + (int(1000 * current_time) % 1000)


def get_linkid(class_id):
    """
    生成linkid
    :param class_id:
    """
    """
    time_stamp = get_timestamp()
    tmp = struct.pack('=ii', time_stamp, class_id)
    linkid = struct.unpack('=Q', tmp)
    return linkid[0]
    """
    return class_id


def pack_full_msg(linkid, msgtype, req_msg, dest_proc_name, eventno, term_code, device_code, trans_id):
    """
    打包处理机接收的二进制消息
    :param linkid: iot msg linkid
    :param msgtype: msgtypedef里定义的消息类型
    :param req_msg: 具体的消息内容
    :param dest_proc_name: 目的pid
    :param eventno: 消息事件号
    :param term_code: 终端类型编号
    :param device_code: 设备类型编号
    :param trans_id: 交易唯一id
    :return:
    """
    # trans is 必须有
    if trans_id is None or trans_id == '':
        return ""

    try:
        iot_msg_dict = {
            TAG_IOT_H_LINKID: linkid,
            TAG_IOT_H_TRANSID: trans_id,
            TAG_IOT_H_MSGTYPE: msgtype,
            TAG_IOT_H_TERM_CODE: term_code,
            TAG_IOT_H_DEVICE_CODE: device_code,
            TAG_IOT_H_MSGLEN: 0,
            TAG_MSG: req_msg
        }

        iot_msg = pack_iot_msg(iot_msg_dict)
        if iot_msg.__len__() <= 0:
            logging.error('pack iot_msg_dict fail!')
            return ""
        else:
            logging.info('pack iot_msg_dict succ!, %s', iot_msg_dict)

        rz_header = {
            TAG_RZ_H_S_NODEID: API_SELF_NODE_ID,
            TAG_RZ_H_SENDER: API_ZMQ_THREAD_NAME,
            TAG_RZ_H_D_NODEID: API_SELF_NODE_ID,
            TAG_RZ_H_DEST: dest_proc_name,
            TAG_RZ_H_EVENTNO: eventno,
            TAG_RZ_H_BUFLEN: iot_msg.__len__(),
            TAG_MSG: iot_msg
        }
        msg = pack_rz_msg(rz_header)
        if msg.__len__() <= 0:
            logging.error('pack rz_msg fail!')
            return ""
        else:
            logging.info('pack rz_msg succ!, %s', rz_header)

    except Exception as e:
        logging.error('pack_full_msg fail!, linkid = %d, msgtype = %s, req_dict = %s, dest_proc_name = %s, eventno = %d, e = %s',
                      linkid, msgtype, req_msg, dest_proc_name, eventno, e)
        msg = ""

    return msg
