# -*- coding: utf-8 -*-

from DistributedLock.distributed_lock import *
import unittest
import memcache
from common.settings import MEMCACHE_HOST
import time

__author__ = 'jxh'


# 测试外部彩信接口
class TestDistributedLock(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNormalLockAndUnlock(self):
        try:
            while True:
                mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)
                lock_name = "test_name"

                ret = distributed_lock_require(mem_handle, lock_name, 3)
                # self.assertEqual(ret, True)
                if ret:
                    print("lock success")
                else:
                    print("lock failed")

                ret = distributed_lock_release(mem_handle, lock_name)
                # self.assertEqual(ret, True)

        except Exception as err_info:
            print("lock test failed %s" % err_info)

    def testLockAtSameTime(self):
        mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)
        lock_name = "test_name"

        ret = distributed_lock_require(mem_handle, lock_name, 3)
        self.assertEqual(ret, True)

        ret = distributed_lock_require(mem_handle, lock_name, 3)
        self.assertEqual(ret, False)

        distributed_lock_release(mem_handle, lock_name)

    def testAutoRelease(self):
        mem_handle = memcache.Client(MEMCACHE_HOST, debug=0)
        lock_name = "test_name"

        ret = distributed_lock_require(mem_handle, lock_name, 10)
        self.assertEqual(ret, True)

        ret = distributed_lock_require(mem_handle, lock_name, 3)
        self.assertEqual(ret, False)

        time.sleep(3)

        ret = distributed_lock_require(mem_handle, lock_name, 3)
        self.assertEqual(ret, True)

        distributed_lock_release(mem_handle, lock_name)
