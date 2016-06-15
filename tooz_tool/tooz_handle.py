# coding: utf-8
__author__ = 'Ennis'

import subprocess
import time
from tooz import coordination
from settings import *
from comm_func import *


class ToozHandler:
    """
    Open stack tooz handler class, use to init a tooz client and start to watch, and selected a leader to start
    the process
    """
    def __init__(self, start_command, group_name):
        self.tooz_client = None
        self.child_process = None
        self.__start_command = start_command
        self.__group_name = group_name

    def start_tooz(self):
        """
        start the tooz client
        :return:
        """
        try:
            local_ip = get_local_ip()
            user_name = getpass.getuser()
            member_name = local_ip + '_' + user_name + '_' + self.__group_name
            self.tooz_client = coordination.get_coordinator(MEMCACHE_CFG, member_name.encode())
        except Exception as group_info:
            logging.error('get group info fail as %s', group_info)
            return

        try:
            self.tooz_client.start()

            create_result = self.__create_group_by_name()
            if create_result is False:
                self.tooz_client.stop()
                logging.error('create group fail by [%s]', self.__group_name)
                return

            def group_joined(event):
                logging.info('%s  joined group %s', event.member_id.decode(), event.group_id.decode())
                logging.info('current group leader is: %s ', self.tooz_client.get_leader(self.__group_name.encode()).get())

            def group_leaved(event):
                logging.info('%s  leaved group %s', event.member_id.decode(), event.group_id.decode())

            def when_i_am_elected_leader(event):
                # event is a LeaderElected event
                logging.info('group %s  has elected leader %s', event.group_id.decode(), event.member_id.decode())

                self.child_process = subprocess.Popen(self.__start_command, shell=True)

            self.tooz_client.watch_join_group(self.__group_name.encode(), group_joined)
            self.tooz_client.watch_leave_group(self.__group_name.encode(), group_leaved)
            self.tooz_client.watch_elected_as_leader(self.__group_name.encode(), when_i_am_elected_leader)
            self.tooz_client.join_group(self.__group_name.encode()).get()
        except Exception as e:
            logging.error("ERROR: %s", e)
            return

        self.__while_loop_for_watch()

    def __create_group_by_name(self):
        """
        create the group by group name, if exist return true
        :return:
        """
        try:
            request = self.tooz_client.create_group(self.__group_name.encode())
            request.get()
            logging.info('create tooz group success by group_name = %s', self.__group_name)
            return True
        except coordination.GroupAlreadyExist as exist:
            logging.info('create group info = %s', exist)
            return True
        except Exception as fail_info:
            logging.error('create group fail =%s', fail_info)
            return False

    def __while_loop_for_watch(self):
        """
        start the while loop for watch the leader selected
        :return:
        """
        self.tooz_client.run_elect_coordinator()
        logging.info('start while loop for %s', self.__group_name)
        try:
            while True:
                self.tooz_client.heartbeat()
                self.tooz_client.run_watchers()
                try:
                    if self.child_process is not None:
                        ret = self.child_process.poll()
                        if ret is not None:
                            logging.info('child_process poll = %s, kill child process', ret)
                            kill_running_process(self.__group_name)
                            self.tooz_client.stop()
                            self.tooz_client.start()
                            self.child_process = None
                except Exception as e:
                    logging.error('child_process poll err = %s ', e)
                time.sleep(1)
                logging.debug('group leader is: %s ', self.tooz_client.get_leader(self.__group_name.encode()).get())
        except KeyboardInterrupt:
            if self.child_process is not None:
                logging.info("kill child")
                self.child_process.kill()
            self.tooz_client.leave_group(self.__group_name.encode()).get()
            self.tooz_client.stop()
