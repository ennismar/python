# coding: utf8
__author__ = 'Ennis'

"""
objective: tooz_tool
for local:
    run command "fab local_run"
    will update the tooz_tool from svn, then do py_release, and tar as tooz_tool.tar.gz to commit
    to the svn

for remote:
    run command "fab remote_run"
    will update tooz_tool.tar.gz on 192.168.1.201:iot111, 192.168.1.201:iot222, 192.168.1.202:iot1, 192.168.1.200:iot
    and replace the tooz_tool folder except settings.py, and will kill the process if running

for only one remote:
    run command "fab remote_201_1","fab remote_201_2","fab remote_202" or "fab remote_200"

for local and remote:
    run command "fab run_fab"
    do both for local and for remote
"""


from fabric.api import *
import datetime

SOURCE_DIR = 'tooz_tool'
SOURCE_SVN_DIR = 'tooz_tool_svn'
RELEASE_DIR = 'serv_release'
TAR_NAME = SOURCE_DIR + '.tar.gz'
EX_INCLUDE_FILES = 'settings.py'
START_FILE = 'start_tooz_tool.pyc'


env.roledefs = {
            'server201_1': ['iot111@192.168.1.201:22', ],
            'server201_2': ['iot222@192.168.1.201:22', ],
            'server202': ['iot1@192.168.1.202:22', ],
            'server200': ['iot@192.168.1.200:22', ]
            }

env.passwords = {'iot111@192.168.1.201:22': 'iot111',
                 'iot222@192.168.1.201:22': 'iot222',
                 'iot1@192.168.1.202:22': 'iot1',
                 'iot@192.168.1.200:22': 'iot'}


def local_update_from_svn():
    with lcd('~/%s' % SOURCE_SVN_DIR):
        local('svn up')


def local_copy_source():
    with lcd('~'):
        local('rm -rf %s' % SOURCE_DIR)
        local('cp -av %s %s' % (SOURCE_SVN_DIR, SOURCE_DIR))


def local_py_release():
    with lcd('~'):
        local('py_release -s %s -e %s' % (SOURCE_DIR, EX_INCLUDE_FILES))


def local_tar_package():
    local('rm -rf ~/%s/%s' % (RELEASE_DIR, TAR_NAME))
    with lcd('~'):
        local('mv %s %s/' % (TAR_NAME, RELEASE_DIR))


def local_svn_commit():
    with lcd('~/%s' % RELEASE_DIR):
        time = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        local('svn commit -m %s %s' % (time, TAR_NAME))


def local_run():
    local_update_from_svn()
    local_copy_source()
    local_py_release()
    local_tar_package()
    local_svn_commit()


def remote_svn_up():
    with cd('~/%s' % RELEASE_DIR):
        run('svn up')


def remote_back_setting():
    with settings(warn_only=True):
        if run('cp ~/%s/settings.py ~/settings.py' % SOURCE_DIR).failed:
            print("no this file to copy ,skip")
            return
    run('rm -rf ~/%s' % SOURCE_DIR)


def remote_untar():
    with cd('~/%s' % RELEASE_DIR):
        run('tar -xzvf %s -C ~' % TAR_NAME)

    with settings(warn_only=True):
        if run('mv ~/settings.py ~/%s/' % SOURCE_DIR).failed:
            print("no this file to move ,skip")
            return


def remote_kill_and_run():
    with cd('~/%s' % SOURCE_DIR):
        run('.stop %s' % START_FILE)
        # next command cannot start
        # run('nohup python3 start_smcardhttpserv.pyc &')


def remote_execute_all():
    remote_svn_up()
    remote_back_setting()
    remote_untar()
    remote_kill_and_run()


@roles('server201_1')
def remote_201_1():
    remote_execute_all()


@roles('server201_2')
def remote_201_2():
    remote_execute_all()


@roles('server202')
def remote_202():
    remote_execute_all()


@roles('server200')
def remote_200():
    remote_execute_all()


def remote_run():
    execute(remote_201_1)
    execute(remote_201_2)
    execute(remote_200)
    execute(remote_202)


def run_fab():
    local_run()
    remote_run()
