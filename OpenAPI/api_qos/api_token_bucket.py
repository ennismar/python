# -*- coding: utf-8 -*-
import memcache
import datetime
from common.mongo_utils import *
from common.settings import *
from DistributedLock.distributed_lock import distributed_lock_require, distributed_lock_release
import tornado
from tornado import ioloop

__author__ = 'gz'

COL_APP_INFO = 'app_info'

TAG_APP_NAME = 'app_name'
TAG_APP_KEY = 'appkey'

RATE_KEY_FORMAT = '_max_rate_{}_{}'


class TokenBucket:
    def __init__(self, api_type):
        """
        初始化
        :param api_type: (string)需要控制流量的接口类型 sms/mms/...
        :return:
        """
        self.api_type = api_type
        self.IOLoop = tornado.ioloop
        self.mc = memcache.Client(MEMCACHE_HOST, debug=1)
        self.timer = TOKEN_TIMER * 1000  # ms
        self.default_rate = 0
        self.app_rates = {}
        self.scheduler = None

        if not self._token_init():
            raise Exception('TokenBucket token init fail')

    def _token_init(self):
        """
        初始化各应用令牌数量
        :return:
        """
        try:
            self.app_rates = {}
            # 遍历app_info表获取应用令牌速率
            docs = mongo_cli[DB_IOT][COL_APP_INFO].find()
            for doc in docs:
                app_key = doc.get(TAG_APP_KEY, None)
                if app_key is None:
                    logging.error('app[%s] has no app_key', doc.get(TAG_APP_NAME, 'Unknown'))
                    continue

                # MemCache中初始化应用令牌数
                mc_key = RATE_KEY_FORMAT.format(app_key, self.api_type)
                self.mc.set(mc_key, 0)
                logging.debug('update app[%s] [%s] rate to [0]', app_key, self.api_type)
            return True
        except Exception as err:
            logging.error("%s_token_init error: %s", self.api_type, err)
            return False

    def _update_app_rate(self):
        """
        更新各应用速率
        :return:
        """
        try:
            self.app_rates = {}
            self.default_rate = int(self.mc.get('sys_{}_rate'.format(self.api_type)))
            # 遍历app_info表获取应用令牌速率
            docs = mongo_cli[DB_IOT][COL_APP_INFO].find()
            for doc in docs:
                app_key = doc.get(TAG_APP_KEY, None)
                if app_key is None:
                    logging.error('app[%s] has no app_key', doc.get(TAG_APP_NAME, 'Unknown'))
                    continue

                # 有单独配置使用单独配置，否则使用系统配置
                app_rate = doc.get(self.api_type + '_rate', self.default_rate)
                if app_rate not in self.app_rates.keys():
                    self.app_rates[app_rate] = []
                self.app_rates[app_rate].append(app_key)

                logging.debug('update app[%s] [%s] rate to [%d]', app_key, self.api_type, app_rate)
            return True
        except Exception as err:
            logging.error("%s_token_init error: %s", self.api_type, err)
            return False

    def start(self):
        """
        启动周期运行任务
        :return:
        """
        try:
            self.scheduler = tornado.ioloop.PeriodicCallback(self._add_token, self.timer)
            self.scheduler.start()
        except Exception as err:
            logging.error('>>>>>> start <%s> token bucket scheduler error: %s <<<<<<', self.api_type, err)
            return False

        if self.scheduler.is_running():
            logging.info('>>>>>> start <%s> token bucket scheduler success <<<<<<', self.api_type)
            return True
        else:
            logging.fatal('>>>>>> start <%s> token bucket scheduler failed <<<<<<', self.api_type)
            return False

    def _add_token(self):
        """
        增加应用令牌
        :return:
        """
        logging.info('>>>>>> add app <%s> token at %s <<<<<<<', self.api_type, datetime.datetime.now())
        try:
            # 更新系统配置
            self._update_app_rate()

            for rate, app_list in self.app_rates.items():
                for app_key in app_list:
                    # 获取分布式锁，失败不增加令牌
                    lock_name = app_key + '_' + self.api_type
                    ret = distributed_lock_require(self.mc, lock_name, DISTRIBUTE_LOCK_TIME)
                    if not ret:
                        logging.error("get app[%s] <%s> distributed lock fail", app_key, self.api_type)
                        continue

                    # 获取当前令牌数
                    mc_key = RATE_KEY_FORMAT.format(app_key, self.api_type)
                    token = self.mc.get(mc_key)
                    if token is None:
                        # 没获取应该是新加应用，认为之前为0
                        token = 0

                    # token上限为rate*1s
                    token = int(token) + int(rate * TOKEN_TIMER)
                    if token > rate:
                        token = rate
                    self.mc.set(mc_key, token)

                    # 释放分布式锁
                    distributed_lock_release(self.mc, lock_name)

                    logging.debug('add app[%s] <%s> token to [%d]', app_key, self.api_type, token)
        except Exception as err:
            logging.error("start token add scheduler fail, err: %s", err)
