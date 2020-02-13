import os
from prometheus_client import multiprocess


def child_exit(server, worker):
    multiprocess.mark_process_dead(worker.pid)


if os.environ.get('MODE') == 'dev':
    reload = True

bind = '0.0.0.0:5000'
workers = 4
threads = 4
