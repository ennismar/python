# -*- coding: utf-8 -*-
from fabric.api import local, lcd, env, roles, cd, run, execute, settings
import datetime

__author__ = 'gz'

env.roledefs = {
    'remote_server': ['iot@192.168.1.200:22', 'iot111@192.168.1.201:22', 'iot222@192.168.1.201:22', 'iot@192.168.1.202:22'],
}

env.passwords = {
    'iot@192.168.1.200:22': 'iot',
    'iot111@192.168.1.201:22': 'iot111',
    'iot222@192.168.1.201:22': 'iot222',
    'iot@192.168.1.202:22': 'iot',
}

PROJECT_NAME = 'httpclient'
SETTING_DIR = '~/httpclient/common/'
RELEASE_DIR = '~/serv_release/'
RELEASE_NAME = 'httpclient.tar.gz'
EXCLUDE_FILE = 'settings.py,proc.json'


def local_src_update():
    """
    从svn更新源码
    :return:
    """
    local('svn up')


def local_src_ci():
    """
    提交本地代码到svn
    :return:
    """
    local('svn ci -m %s' % datetime.datetime.now())


def tar_release():
    """
    生成源码tar包
    :return:
    """
    with lcd('~'):
        local('py_release -s %s -e %s' % (PROJECT_NAME, EXCLUDE_FILE))


def local_tar_ci():
    """
    提交tar包到svn
    :return:
    """
    with lcd(RELEASE_DIR):
        local('mv ~/%s %s' % (RELEASE_NAME, RELEASE_DIR))
        local('svn ci %s -m %s' % (RELEASE_NAME, datetime.datetime.now()))


@roles('remote_server')
def remote_tar_update():
    """
    远程主机更新tar包
    :return:
    """
    with cd(RELEASE_DIR):
        run('svn up')


@roles('remote_server')
def remote_tar_unpack():
    """
    远程主机解压tar包
    :return:
    """
    with settings(warn_only=True):
        run('mv %sproc.json %sproc.json.bak' % (SETTING_DIR, SETTING_DIR))
        run('mv %ssettings.py %ssettings.py.bak' % (SETTING_DIR, SETTING_DIR))
    run('tar -zxvf %s -C ~' % (RELEASE_DIR + RELEASE_NAME))


def local_ver_ci():
    """
    提交本地源码及tar包版本
    :return:
    """
    local_src_update()
    local_src_ci()
    tar_release()
    local_tar_ci()


def remote_deploy():
    """
    远程主机部署
    :return:
    """
    execute(remote_tar_update)
    execute(remote_tar_unpack)


def run_fab():
    """
    本地更新&远程部署
    :return:
    """
    local_ver_ci()
    remote_deploy()
