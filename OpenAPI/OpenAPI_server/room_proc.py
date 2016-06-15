# -*- coding: utf-8 -*-
__author__ = 'neo'


from common.mongo_utils import *
from common.api_tagdef import *
from common.iot_msg import *
from common.iot_request_handler import IotRequestHandler


# room 查询
class QueryRooms(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self):
        try:
            condition = {
                TAG_BUILDING_CODE: self.get_argument(TAG_BUILDING_CODE, default=''),
                Q_OFFSET: self.get_argument(Q_OFFSET, default='0'),
                Q_LIMIT: self.get_argument(Q_LIMIT, default='10'),
            }
            resp = query_rooms(self, condition)
            logging.info('query_rooms, condition = %s, result = %s', condition, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_rooms fail! err = %s', err)


# room 详细信息查询
class QueryRoomInfo(IotRequestHandler):
    def data_received(self, chunk):
        pass

    def get(self, room_code):
        try:
            resp = query_room_info(self, room_code)
            logging.info('query_room_info, reader_code = %s, result = %s', room_code, resp)
            self.write(resp)
            self.finish()
        except Exception as err:
            self.set_status(500)
            self.write({"status": 1000, "status_text": "Internal system error"})
            self.finish()
            logging.error('query_room_info fail! err = %s', err)


def query_rooms(httpinstance, condition):
    """
    查询rooms列表
    :param httpinstance:
    :param condition:
    """
    resp = {
        Q_LIMIT: int(condition[Q_LIMIT]),
        Q_OFFSET: int(condition[Q_OFFSET]),
        Q_TOTAL: 0
    }

    qc = {}
    if condition[TAG_BUILDING_CODE] != '':
        qc[TAG_BUILDING_CODE] = condition[TAG_BUILDING_CODE]

    count = 0
    try:
        # 获取总条数
        count = mongo_cli[DB_IOT]['room_info'].find(qc, {TAG_ROOM_DESC: 1, TAG_ROOM_COORDINATE: 1}).count()
    except Exception as err:
        httpinstance.set_status(500)
        logging.info("Can't find room, condition = %s, err = %s", condition, err)
        return count, resp

    if count > 0:
        try:
            # 获取数据集
            results = mongo_cli[DB_IOT]['room_info'].find(qc, {TAG_ROOM_DESC: 1, TAG_ROOM_COORDINATE: 1, TAG_ROOM_CODE: 1}).sort("_id", SORT_DESC)\
                .skip(int(condition[Q_OFFSET])).limit(int(condition[Q_LIMIT]))

            room_list = []
            for one_room in results.__iter__():
                if "_id" in one_room.keys():
                    del one_room["_id"]

                one_room['herf'] = '/rooms/' + one_room[TAG_ROOM_CODE]
                room_list.append(one_room)

            resp = {
                Q_LIMIT: int(condition[Q_LIMIT]),
                Q_OFFSET: int(condition[Q_OFFSET]),
                Q_TOTAL: count,
                TAG_ROOMS: room_list
            }
        except Exception as err:
            httpinstance.set_status(500)
            logging.error('query_c = %s, Exception = %s', condition, err)

    return resp


def query_room_info(httpinstance, room_code):
    """
    查询room详细信息
    :param httpinstance:
    :param room_code:
    :return:
    """
    resp = ""
    try:
        info = mongo_cli[DB_IOT]['room_info'].find_one({TAG_ROOM_CODE: room_code}, {"_id": 0})
        if info is None:
            resp = {"status": 1000, "status_text": "unregistered room"}
        else:
            resp = info
    except Exception as err:
        httpinstance.set_status(500)
        logging.error('query_location_info fail!, room_code = %s, e = %s', room_code, err)

    return resp
