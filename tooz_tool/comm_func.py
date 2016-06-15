# coding: utf-8
__author__ = 'Ennis'

import socket
import logging
import netifaces
import struct
# import fcntl
import psutil
import getpass


def get_local_ip():
    """
    Returns local ip
    """
    try:
        # gws = netifaces.gateways()
        # interface = gws['default'][netifaces.AF_INET][1]
        # logging.info('get the interface for get ip is [%s]', interface)
        # s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # loc_ip = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915,
        #                                       struct.pack('128s', interface.encode()))[20:24])
        # logging.info("get local ip is %s", loc_ip)
        return 'loc_ip'
    except Exception as socket_error:
        logging.error('get local ip fail as %s', socket_error)
        return "127.0.0.1"


def kill_running_process(process_name):
    """
    get the all pids,then filter out the process we need by process_name and kill the process
    :param process_name:
    """
    try:
        user = getpass.getuser()
        logging.info('get the user name is [%s]', user)
        all_pid = psutil.pids()
        for pid in all_pid:
            pid_info = psutil.Process(pid)
            if process_name in pid_info.cmdline() and user == pid_info.username():
                logging.info('get the pid [%s] by process name [%s]', pid, process_name)
                pid_info.kill()
                logging.info('kill the pid [%s] by process name [%s]', pid, process_name)

    except Exception as e:
        logging.error('get_process_pid fail = %s', e)


def get_process_name(command_str):
    """
    get the process name
    :param command_str:
    :return:process name
    """
    try:
        # split by space
        str_dic = command_str.split(' ')
        if len(str_dic) < 2:
            logging.error('start command is illegal [%s]', command_str)
            return None

        if 'process' in command_str:
            # start like process reader_ctrl
            logging.info('get the process name [%s] from [%s]', str_dic[1], command_str)
            return str_dic[1]
        else:
            # start like device_notify
            logging.info('get the process name is [%s] from [%s]', str_dic[0], command_str)
            return str_dic[0]
    except Exception as e:
        logging.error('get_python_process_name fail =%s', e)
        return None