# -*- coding: utf-8 -*-
__author__ = 'neo'

import logging
import pymongo

from common.settings import MONGO_HOST, IS_DEBUG, MONGO_HOST_DEBUG
from common.decryption import decry

DB_IOT = 'iot'
SORT_ASC = pymongo.ASCENDING
SORT_DESC = pymongo.DESCENDING

try:
    if IS_DEBUG != 1:
        mongodechost = list(map(decry, MONGO_HOST))
        logging.info(mongodechost)
        mongo_cli = None
        if not all(mongodechost):
            logging.info("decryption failed")
        else:
            mongo_cli = pymongo.MongoClient(mongodechost)
    else:
        mongo_cli = pymongo.MongoClient(MONGO_HOST_DEBUG)
except Exception as e:
    logging.error("Can't connect to mongodb! %s", e)
