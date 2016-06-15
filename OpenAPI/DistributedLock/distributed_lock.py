# -*- coding: utf-8 -*-
author = "jxh"

import logging

LOCK_PREFIX = "distributed_lock_"


def distributed_lock_require(mem_client, lock_name, expire):
    """
    # 获取锁操作
    :param mem_client:  memcache客户端
    :param lock_name: 锁的名称
    :param expire: 超时时间，单位为秒
    :return: 加锁成功返回True
              加锁失败返回False
    """
    if mem_client is None or lock_name is None or expire is None:
        logging.error("The param is wrong")
        return False

    key_name = LOCK_PREFIX + lock_name
    try:
        mem_client
        result = mem_client.add(key_name, expire, time=expire)
        if result != 0:
            return True
        else:
            return False
        mem_client.delete(key_name, time=expire)

    except Exception as err_info:
        logging.error("require the lock failed: %s" % err_info)
        return False


def distributed_lock_release(mem_client, lock_name):
    """
    # 释放锁操作
    :param mem_client: memcache客户端
    :param lock_name: 锁的名称
    :return: 解锁成功返回True
              解锁失败返回False
    """
    if mem_client is None or lock_name is None:
        logging.error("The param is wrong")
        return False

    key_name = LOCK_PREFIX + lock_name
    try:
        result = mem_client.delete(key_name)
        if result != 0:
            return True
        else:
            return False
    except Exception as err_info:
        logging.error("release the lock failed: %s" % err_info)
        return False


def distributed_check_expiration(mem_client, lock_name):
    """
    # 测试锁是否存在
    :param mem_client: memcache客户端
    :param lock_name: 锁的名称
    :return: 已过期返回True
              未过期返回False
    """
    if mem_client is None or lock_name is None:
        logging.error("The param is wrong")
        return False

    key_name = LOCK_PREFIX + lock_name
    try:
        value = mem_client.get(key_name)
        if value is None:
            return True
        else:
            return False

    except Exception as err_info:
        logging.error("check the lock expire failed: %s" % err_info)
        return False