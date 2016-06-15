# -*- coding: utf-8 -*-
__author__ = 'neo'

import hashlib
import base64
import datetime
import re
from common.mongo_utils import *
from common.api_tagdef import *
from common.iot_msg import TAG_IOT_H_TRANSID
from common.settings import API_SELF_NODE_ID
from common.call_log import insert_call_log


def set_is_check_auth(is_check_auth):
    # 是否进行basic验证
    global IS_CHECK_AUTH
    IS_CHECK_AUTH = is_check_auth
    logging.info('Openapi check Authorization = %s', IS_CHECK_AUTH)


def _check_auth(appkey, x):
    """
    :param appkey:
    :param x:
    :return:
    """
    logging.debug('Auth:is_check = %s,  %s, %s', IS_CHECK_AUTH, appkey, x)

    # 如果不需要basic验证，直接返回成功
    if IS_CHECK_AUTH is False:
        return True

    try:
        # 从app_info表中获取token，app_secret
        app_info = mongo_cli[DB_IOT]['app_info'].find_one({TAG_APPKEY: appkey}, {TAG_TOKEN: 1, TAG_APPSECRET: 1})
        if app_info is None:
            logging.debug('appkey is invalid! appkey = %s', appkey)
            return False
        valid_x = hashlib.sha1((app_info[TAG_TOKEN] + app_info[TAG_APPSECRET]).encode()).hexdigest()
        if x == valid_x:
            return True
        else:
            return False
    except Exception as err:
        logging.error('appkey = %s, x = %s, Exception = %s', appkey, x, err)
        return False


def http_basic_auth(handler_class):
    """
    http basic Authorization
    :type handler_class: tornado.web.RequestHandler
    :param handler_class:
    :return:

    # Should return the new _execute function, one which enforces
    # authentication and only calls the inner handler's _execute() if
    # it's present.
    """
    def wrap_execute(handler_execute):
        def require_auth(handler, kwargs):
            """
            :param handler:
            :param kwargs:
            :return:

            # I've pulled this out just for clarity, but you could stick
            # it in _execute if you wanted.  It returns True iff
            # credentials were provided.  (The end of this function might
            # be a good place to see if you like their username and
            # password.)
            """
            auth_header = handler.request.headers.get('Authorization')

            if auth_header is None or not auth_header.startswith('Basic '):
                # If the browser didn't send us authorization headers,
                # send back a response letting it know that we'd like
                # a username and password (the "Basic" authentication
                # method).  Without this, even if you visit put a
                # username and password in the URL, the browser won't
                # send it.  The "realm" option in the header is the
                # name that appears in the dialog that pops up in your
                # browser.

                handler.set_status(401)
                handler.set_header('WWW-Authenticate', 'Basic realm=Restricted')
                handler._transforms = []
                handler.finish()
                return False

            # The information that the browser sends us is
            # base64-encoded, and in the format "username:password".
            # Keep in mind that either username or password could
            # still be unset, and that you should check to make sure
            # they reflect valid credentials!
            auth_decoded = base64.b64decode(auth_header[6:]).decode()
            appkey, x = auth_decoded.split(':', 2)

            auth_found = _check_auth(appkey, x)
 
            if auth_found is False:
                handler.set_status(401)
                handler.set_header('WWW-Authenticate', 'Basic realm=Restricted')
                handler._transforms = []
                handler.finish()
                return False
            else:
                # 特殊接口调用鉴权
                ret = user_api_auth(handler.request.uri, appkey)
                if not ret:
                    handler.set_status(405)
                    handler._transforms = []
                    handler.write({"status": 405, "status_text": "Method Not Allowed"})
                    handler.finish()
                    return False

                # http header 增加相关信息，以便处理逻辑中方便获取
                handler.request.headers.add('auth', auth_found)
                handler.request.headers.add(TAG_APPKEY, appkey)
                handler.request.headers.add(TAG_IOT_H_TRANSID, 'APISERV' + str(API_SELF_NODE_ID)
                                            + datetime.datetime.now().strftime('%Y%m%d%H%M%S%f'))

                # 记录日志
                insert_call_log(appkey, handler)
 
            return True

        def _execute(self, transforms, *args, **kwargs):
            """
            :param self:
            :param transforms:
            :param args:
            :param kwargs:
            :return:

            # Since we're going to attach this to a RequestHandler class,
            # the first argument will wind up being a reference to an
            # instance of that class.
            """
            if not require_auth(self, kwargs):
                return False
            return handler_execute(self, transforms, *args, **kwargs)
 
        return _execute
 
    handler_class._execute = wrap_execute(handler_class._execute)
    return handler_class


def user_api_auth(request_uri, app_key):
    """
    app用户api调用鉴权
    :param request_uri:
    :param app_key:
    :return:
    """
    try:
        # 获取应用开发者devcode
        result = mongo_cli[DB_IOT]['app_info'].find_one({TAG_APPKEY: app_key}, {'devcode': 1, '_id': 0})
        # 应用没有devcode只能调用普通接口
        if not result:
            logging.info('app[%s] has no developer code', app_key)
            return False

        # 获取开发者已授权特殊接口
        dev_code = result['devcode']
        dev_info = mongo_cli[DB_IOT]['developer_info'].find_one({'devcode': dev_code})
        # 未找到开发者
        if not dev_info:
            logging.error("developer info not found, devcode=[%s]", dev_code)
            return False

        # 开发者账户未审核通过禁止调用api
        if dev_info['applyFlag'] != 2:
            logging.error("developer applyFlag error, devcode=[%s], applyFlag=[%d]", dev_code, dev_info['applyFlag'])
            return False

        # 获取特殊接口列表
        special_api = mongo_cli[DB_IOT]['openapi_info'].find({'status': 1}, {'uri': 1, '_id': 0})
        # 没有特殊接口返回成功
        if not special_api:
            return True
        # 是特殊接口下一步处理，否则直接返回成功
        for api in special_api:
            pattern = api['uri']
            if not pattern.endswith('$'):
                pattern += '$'
            if re.match(pattern, request_uri):
                break
        else:
            return True

        # 接口在开发者已授权列表返回成功，否则返回失败
        for api in dev_info['available_apis']:
            pattern = api['uri']
            if not pattern.endswith('$'):
                pattern += '$'
            if re.match(pattern, request_uri):
                return True
        else:
            logging.error("method not allowed, appkey=[%s]", app_key)
            return False

    except Exception as err:
        logging.error("user_api_auth error:[%s]", err)
        return False


def resource_auth(appkey, resource_type, resource_code = None, appid = None):
    """
    资源访问权限管理函数
    增、删、改权限在后台实际处理的逻辑里控制
    查询逻辑：
    自身资源可访问
    其他资源根据Authorize_info表配置进行管理
    :param appkey: 资源访问者appkey
    :param resource_type: 资源类型
    :param resource_code: 访问的资源编码，可能为None
    :param appid: 资源拥有者appid，没有appid，表示只访问自有资源

    :return appkey: 返回可访问的appkey
    """
    # 查询appid对应的appkey
    # 如果有resource_code，则根据resource_code查询，否则根据appid查询
    if resource_code is None:
        # 如果appid为空，则默认访问自有资源，通过appkey查询appid
        if appid is not None and appid is not '':
            try:
                info = mongo_cli[DB_IOT]['app_info'].find_one({TAG_APPID: appid}, {TAG_APPKEY: 1, "_id": 0})
                if info is None:
                    logging.warning('appid is invalid, appid = %s', appid)
                    return None
                else:
                    searched_appkey = info[TAG_APPKEY]
                    # logging.DEBUG('app_info get appid = %s, searched_appkey = %s', appid, searched_appkey)
            except Exception as err:
                logging.error('search appkey by appid fail!, appid = %s, e = %s', appid, err)
                return None
        else:
            searched_appkey = appkey
            # logging.DEBUG('appid = %s, searched_appkey = %s', appid, searched_appkey)
    else:
        if resource_type == 'reader':
            table_name = 'reader_info'
            tag_name = 'reader_code'
        elif resource_type == 'camera':
            table_name = 'camera_info'
            tag_name = 'camera_code'
        elif resource_type == 'pos':
            table_name = 'pos_info'
            tag_name = 'pos_code'
        elif resource_type == 'idcard':
            table_name = 'idcard'
            tag_name = 'idcard_code'
        elif resource_type == 'access_controller':
            table_name = 'access_controller'
            tag_name = 'access_controller_code'
        elif resource_type == 'app_data':
            table_name = 'app_data'
            tag_name = 'data_code'
        elif resource_type == 'sensornode':
            table_name = 'sensornode_info'
            tag_name = 'node_code'
        elif resource_type == 'sensor':
            table_name = 'sensor_info'
            tag_name = 'sensor_code'
        elif resource_type == 'trigger':
            table_name = 'triggers'
            tag_name = 'trigger_code'
        elif resource_type == "timertask":
            table_name = "op_schedule"
            tag_name = "task_code"
        else:
            logging.error("resource_type is invalid!, resource_type = %s", resource_type)
            return None

        try:
            info = mongo_cli[DB_IOT][table_name].find_one({tag_name: resource_code}, {TAG_APPKEY: 1, "_id": 0})
            if info is None:
                logging.warning('resource_code is invalid, resource_type = %s, resource_code = %s', resource_type, resource_code)
                return None
            else:
                searched_appkey = info[TAG_APPKEY]
                # logging.DEBUG('table %s get searched_appkey = %s', table_name, searched_appkey)
        except Exception as err:
            logging.error('search appkey by appid fail!, appid = %s, e = %s', appid, err)
            return None

    # 访问自身资源，直接返回自身appkey
    if searched_appkey == appkey:
        return searched_appkey

    # 查询appkey访问权限配置
    try:
        # logging.DEBUG('query authorize_info, qc = {owner_appkey: %s, authorize_appkey: %s}', searched_appkey, appkey)
        authorize_info = mongo_cli[DB_IOT]['authorize_info'].find_one({'owner_appkey': searched_appkey, 'authorize_appkey':appkey})
        if authorize_info is None:
            return None
        else:
            # logging.DEBUG('authorize_info = %s', authorize_info)
            if resource_type in authorize_info['device_type_list']:
                expire_time = authorize_info['expire_time'] #datetime.datetime.strptime(authorize_info['expire_time'], '%Y-%m-%d %H:%M:%S')
                if expire_time <= datetime.datetime.now():
                    try:
                        mongo_cli[DB_IOT]['authorize_info'].remove({'owner_appkey': searched_appkey, 'authorize_appkey':appkey})
                    except Exception as err:
                        logging.error('delete authorize_info fail! {owner_appkey: %s, authorize_appkey:%s}, err = %s', searched_appkey, appkey, err)
                        return None
                else:
                    return searched_appkey
            else:
                return None
    except Exception as err:
        logging.error('search authorize_info fail! err = %s', err)
        return None
