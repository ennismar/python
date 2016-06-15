# coding: utf-8
__author__ = 'Ennis'

from settings import *
from comm_func import *
from DistributedLock.distributed_lock import *
import memcache
import subprocess
import time


class ProcessHandler:
    """
    manage the process
    """
    def __init__(self, start_command, group_name):
        self.mem_client = memcache.Client(MEMCACHE_CFG, debug=0)
        self.child_process = None
        self.group_name = group_name
        self._start_command = start_command

    def start_process(self):
        """
        :return:
        """
        try:
            try:
                local_ip = get_local_ip()
                user_name = getpass.getuser()
                member_name = local_ip + '_' + user_name + '_' + self.group_name
                group_set = "GROUP_SET_" + self.group_name
            except Exception as err:
                logging.error("get local info fail = %s", err)
                return
            while True:
                try:

                    # check the memcache lock
                    if distributed_check_expiration(self.mem_client, self.group_name) is True:
                        # group name is not lock
                        if distributed_lock_require(self.mem_client, self.group_name, MEMCACHE_EXPIRE) is True:
                            # require lock and start process
                            self.child_process = subprocess.Popen(self._start_command, shell=True)
                            self.mem_client.set(group_set, member_name)
                            logging.info("start the process = %s", member_name)

                    if self.child_process is not None:
                        ret = self.child_process.poll()

                        if ret is not None:
                            logging.info('child_process poll = %s, kill child process', ret)
                            kill_running_process(self.group_name)
                            self.child_process = None
                            distributed_lock_release(self.mem_client, self.group_name)
                        else:
                            distributed_update_expiration(self.mem_client, self.group_name, MEMCACHE_EXPIRE)

                    current_run = self.mem_client.get(group_set)
                    logging.debug("current running is %s", current_run)
                except Exception as e:
                    logging.error('child_process poll err = %s ', e)

                time.sleep(2)

        except KeyboardInterrupt:
            logging.info("KeyboardInterrupt will stop the process")
            if self.child_process is not None:
                logging.info("kill child")
                self.child_process.kill()
                distributed_lock_release(self.mem_client, self.group_name)
