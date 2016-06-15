# -*- coding: utf-8 -*-
__author__ = 'neo'

import json

from common.mongo_utils import *
from common.api_tagdef import *
from common.iot_msg import *
from common.iot_request_handler import IotRequestHandler

# 按楼宇编号查询building
class QueryBuildingBySerial(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, serial):
        try:
            resp = query_building_by_serial(self, serial)
            logging.info('query_building_by_serial, serial = %s, result = %s', serial, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_building_by_serial fail! err = %s', err)

# building location 查询
class QueryLocations(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    def get(self):
        try:
            condition = {
                TAG_BUILDING_NAME: self.get_argument(TAG_NAME, default=''),
                TAG_COORDINATE: self.get_argument(TAG_COORDINATE, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
            }
            resp = query_locations(self, condition)
            logging.info('query_locations, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_locations fail! err = %s', err)


# building location 详细信息查询
class QueryLocationInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    # 加异步装饰器，在处理异步响应后finish连接
    def get(self, location_code):
        try:
            resp = query_location_info(self, location_code)
            logging.info('query_location_info, location_code = %s, result = %s', location_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(501)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_location_info fail! err = %s', err)


def query_locations(handler, condition):
    """
    查询building location列表
    :param handler:
    :param condition:
    """
    resp = {
        Q_LIMIT: int(condition[Q_LIMIT]),
        Q_OFFSET: int(condition[Q_OFFSET]),
        Q_TOTAL: 0
    }

    qc = {}
    if condition[TAG_BUILDING_NAME] != '':
        qc[TAG_BUILDING_NAME] = condition[TAG_BUILDING_NAME]

    if condition[TAG_COORDINATE] != '':
        req_dict = json.loads(condition[TAG_COORDINATE])
        latitude = req_dict.get(TAG_LATITUDE, -9999)
        longitude = req_dict.get(TAG_LONGITUDE, -9999)
        distance = req_dict.get(TAG_DISTANCE, 0)
        if latitude == -9999 or longitude == -9999:
            err = 'query condition is invalid! con == %s' % condition
            logging.error(err)
            return err
        else:
            qc[TAG_COORDINATE] = {
                '$near': '[' + str(latitude) + ',' + str(longitude) + ']',
                '$maxDistance': int(distance)
            }

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['building_info'].find(qc, {TAG_NAME: 1, TAG_COORDINATE: 1}).count()
    except Exception as err:
        handler.set_status(501)
        logging.info("Can't find building, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['building_info'].find(qc, {TAG_NAME: 1, TAG_COORDINATE: 1, TAG_BUILDING_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            building_list = []
            for one_building in results.__iter__():
                if "_id" in one_building.keys():
                    del one_building["_id"]

                one_building['herf'] = '/buildings/' + one_building[TAG_BUILDING_CODE]
                building_list.append(one_building)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_BUILDINGS: building_list
            }
        except Exception as err:
            handler.set_status(501)
            logging.error('query_c = %s, Exception = %s', condition, err)

    return resp


def query_location_info(handler, location_code):
    """
    查询建筑物详细信息
    :param handler:
    :param location_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['building_info'].find_one({TAG_BUILDING_CODE: location_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered building"}
        else:
            resp = info
    except Exception as err:
        handler.set_status(501)
        logging.error('query_location_info fail!, location_code = %s, e = %s', location_code, err)

    return resp


def query_building_by_serial(handler, serial):
    resp = ""
    try:
        query_tag = '{}.{}'.format(TAG_DETAIL_INFO, TAG_SERIAL)
        info = mongo_cli[DB_IOT]['building_info'].find_one({query_tag: serial}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered building"}
        else:
            resp = info
    except Exception as err:
        handler.set_status(501)
        logging.error('query_building_by_serial fail!, serial = %s, e = %s', serial, err)

    return resp
