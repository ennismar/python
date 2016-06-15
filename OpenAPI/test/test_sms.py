# -*- coding: utf-8 -*-
import unittest
import requests
import requests.auth
import json
import hashlib
from test.config import SERV_HOST

__author__ = 'gz'

app_key = 'baa5b2147e3b26209619da3da540ba06'
app_token = 'abcd6'
app_secret = '846ada606477c4cc753d627d4d7f4a9e'
password = hashlib.sha1((app_token + app_secret).encode()).hexdigest()
auth = requests.auth.HTTPBasicAuth(app_key, password)


class TestSmsSend(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testNormal(self):
        sms_info = {
            "dest_telno": "10086",
            "content": "OpenAPI短信接口测试"
        }
        resp = requests.post('http://{}/v1/sms'.format(SERV_HOST), data=json.dumps(sms_info), auth=auth)
        self.assertEqual(resp.status_code, 200)

    def testDstError(self):
        sms_info = {
            "dest_telno": ["10086", "13800138000"],
            "content": "OpenAPI接口测试"
        }
        resp = requests.post('http://{}/v1/sms'.format(SERV_HOST), data=json.dumps(sms_info), auth=auth)
        self.assertEqual(resp.status_code, 200)

        ret = json.loads(resp.text)
        self.assertEqual(ret["status"], 1000)
