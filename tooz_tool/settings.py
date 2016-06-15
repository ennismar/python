# coding: utf-8
__author__ = 'Ennis'

import logging

LOGGING_LEVEL = logging.DEBUG
MEMCACHE_CFG = ['memcached://192.168.1.200:12311']

# 需要启动的进程，c进程以process -d的形式,['device_notify -d','process reader_ctrl -d']
START_COMMAND_DIC = ['device_notifi -d']
