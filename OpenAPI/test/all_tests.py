# -*- coding: utf-8 -*-
__author__ = 'Ryan'

import glob
import unittest
import sys
import datetime
import test.HTMLTestRunner as HTMLTestRunner


def run_all_tests(out=sys.stderr, verbosity=2):
    # 扫描所有test开头的py文件，加载测试用例
    test_file_strings = glob.glob('test*.py')
    module_strings = [module_name[0:len(module_name)-3] for module_name in test_file_strings]
    suits = [unittest.defaultTestLoader.loadTestsFromName(name) for name in module_strings]
    test_suits = unittest.TestSuite(suits)

    # 执行测试用例
    # unittest.TextTestRunner(out, verbosity=verbosity).run(test_suits)
    HTMLTestRunner.HTMLTestRunner(
                stream=out,
                title='OpenAPI接口测试报告',
                description='测试项目由test目录中"test*.py"指定',
                verbosity=verbosity
                ).run(test_suits)


if __name__ == "__main__":
    result_file = 'testing_{}.html'.format(datetime.datetime.now().strftime('%Y%m%d%H%M'))

    with open(result_file, 'w') as f:
        run_all_tests(f)

