# coding: utf-8
__author__ = 'Ennis'

import memcache
import logging

from common.settings import MEMCACHE_HOST

memc_handle = None

#初始化连接memcache
def init_memcache():
    try:
        global memc_handle
        memc_handle = memcache.Client(MEMCACHE_HOST, debug=0)
        logging.info('init memcache : %r', MEMCACHE_HOST)
    except Exception as e:
        logging.error("init memcache error %s", e)

#向memcache中插入值
def set_value_to_memcache(key, value):
    try:
        global memc_handle
        memc_handle.set(key, value)
    except Exception as e:
        logging.error("set memcache error %s", e)

#根据key值获取value值
def get_value_from_memcache(key):
    try:
        global memc_handle
        return memc_handle.get(key)
    except Exception as e:
        logging.error("get memcache error %s", e)

#根据key删除
def delete_value_from_memcache(key):
    try:
        global memc_handle
        memc_handle.delete(key)
    except Exception as e:
        logging.error("delete memcache error %s", e)