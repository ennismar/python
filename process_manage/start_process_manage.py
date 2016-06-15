# coding: utf-8
__author__ = 'Ennis'

import sys
import signal
import threading
import logging.handlers
from settings import *
from comm_func import *
from DistributedLock.distributed_lock import *
from process_handle import ProcessHandler

process_class = []


def init_logging():
    """
    日志文件设置，同时打印在日志文件和屏幕上
    """
    logger = logging.getLogger()
    logger.setLevel(LOGGING_LEVEL)

    sh = logging.StreamHandler()
    file_log = logging.handlers.TimedRotatingFileHandler('process_manage.log', 'MIDNIGHT', 1, 0)
    formatter = logging.Formatter('[%(asctime)s] [%(levelname)-7s] [%(module)s:%(filename)s-%(funcName)s-%(lineno)d] %(message)s')
    sh.setFormatter(formatter)
    file_log.setFormatter(formatter)

    logger.addHandler(sh)
    logger.addHandler(file_log)

    logging.info("Current log level is : %s", logging.getLevelName(logger.getEffectiveLevel()))


def sig_handler(signum, frame):
    logging.info('recv sig = ', signum)
    logging.info('frame', frame)
    for one_process in process_class:
        if one_process.child_process is not None:
            logging.info("kill child")
            one_process.child_process.kill()
            distributed_lock_release(one_process.mem_client, one_process.group_name)
    exit()


def check_python_version():
    if sys.version[:1] != '3':
        return False
    else:
        return True


if __name__ == '__main__':
    try:
        # 检查python版本
        if check_python_version() is False:
            print('Please use python3 run the program')
            exit()

        init_logging()
        signal.signal(signal.SIGABRT, sig_handler)
        signal.signal(signal.SIGTERM, sig_handler)
        signal.signal(signal.SIGINT, sig_handler)

        threads = []

        for start_command in START_COMMAND_DIC:
            process_name = get_process_name(start_command)
            if process_name is None:
                logging.error('get process name fail, please check start command [%s]', start_command)
                sys.exit(1)

            kill_running_process(process_name)

            one_process = ProcessHandler(start_command, process_name)
            global process_class
            process_class.append(one_process)
            thread = threading.Thread(target=one_process.start_process)
            thread.setDaemon(True)
            thread.start()
            threads.append(thread)
            logging.info('start thread by command [%s], process_name=[%s]', start_command, process_name)

        logging.info('waiting for thread loop finish')
        for thread in threads:
            thread.join()
    except Exception as e:
        logging.error('start fail = %s', e)
