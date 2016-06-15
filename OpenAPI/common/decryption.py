# -*- coding: utf-8 -*-
__author__ = 'jxh'

from ctypes import *
import os
import logging

from common.settings import DECODE_LIB

def decry(todecrystr):
    try:
        homepath = os.environ['HOME']
        libpath = DECODE_LIB
        if homepath.endswith("/"):
            libpath = homepath + "lib/" +libpath
        else:
            libpath = homepath + "/lib/" + libpath
        decodelib = CDLL(libpath)
        decrystr = create_string_buffer(1024)
        ctodecrystr = c_char_p(bytes(todecrystr, encoding="utf-8"))
        decodelib.decode_db_passwd(ctodecrystr, decrystr, 1024)
        retstr = str(decrystr, encoding="utf-8")
        strlen = retstr.index("\0")
        retstr = retstr[:strlen]
        return retstr

    except Exception as e:
        logging.info("decry failed e = %s", e)
        return None