# coding: utf-8
__author__ = 'Ennis'

import logging

LOGGING_LEVEL = logging.DEBUG
MEMCACHE_CFG = ['192.168.1.200:30000', '192.168.1.200:31000', '192.168.1.200:32000']

MEMCACHE_EXPIRE = 10

# 需要启动的进程，c进程以process -d的形式,['device_notify -d','process reader_ctrl -d']
START_COMMAND_DIC = ['device_notify -d', 'process reader_ctrl -d']


