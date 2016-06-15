# -*- coding: utf-8 -*-
__author__ = 'neo'

import datetime
import json

from common.api_tagdef import *


def parse_query_conditions(conditions):
    """
    解析请求字符串，组装成mongodb的查询条件dict
    :rtype: dict
    :param conditions:
    """
    qc = {}
    q_dict = json.loads(conditions)
    for k,v in q_dict.items():
        qc[TAG_DATA_INFO + '.' + str(k)] = v

        # 判断value是不是dict
        if isinstance(v, dict) is True:
            # 如果是dict，判断是否时间，如果是时间，转换为datetime类型
            for v_key, v_value in v.items():
                qc[TAG_DATA_INFO + '.' + str(k)][v_key] = v_value

    return qc


def parse_query_result_tag_list(result_tag_list):
    """
    解析请求中的返回字段列表，组装成mongodb的dict
    :rtype: dict
    :param result_tag_list:
    """
    result_dict = {}
    if result_tag_list is None or result_tag_list == '':
        result_dict = {
            TAG_DATA_INFO: 1
        }
    else:
        for one_tag in result_tag_list.split(','):
            tag_name = TAG_DATA_INFO + '.' + one_tag
            result_dict[tag_name] = 1

    return result_dict


def dict_datetime_to_string(dict_value):
    """
    遍历dict，如果value是datetime类型，转换为string
    :param dict_value:
    """
    if isinstance(dict_value, dict):
        for k, v in dict_value.items():
            if isinstance(v, dict):
                dict_datetime_to_string(v)
            else:
                if isinstance(v, datetime.datetime):
                    dict_value[k] = v.strftime('%Y-%m-%d %H:%M:%S')
