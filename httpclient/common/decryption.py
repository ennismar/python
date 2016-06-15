# -*- coding: utf-8 -*-

import os
import logging
from ctypes import *
from common.settings import DECODE_LIB

__author__ = 'gz'


def decrypt(cipher):
    """
    使用librz.so库解密字符串
    :param cipher: 密文字符串
    :return: 原文字符串
    """
    try:
        lib_path = os.path.normpath(os.path.join(os.environ['HOME'], 'lib', DECODE_LIB))
        lib = CDLL(lib_path)
        c_string = create_string_buffer(1024)
        lib.decode_db_passwd(cipher.encode(), c_string, 1024)
        original = c_string.value.decode()
        return original

    except Exception as err:
        logging.info("decrypt failed, error = [%s]", err)
        return None
