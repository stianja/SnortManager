# -*- coding: utf-8 -*-

"""
Logging system activity to file
To log, choose between: debug, info, warning, error and critical

Example: Use "debug("Yourmessage")"

Remember to add "from log import debug, info, warning, error, critical"
in the different modules you want to log from

Remember to specify path for logfile DEBUG_LOG_FILENAME = '/your/path

Log format is: Date(timestamp) Modulename : Message
"""


import logging
import sys
import os
from webapp.config import DATADIR

log_dir = os.path.join(DATADIR, 'logs')


formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(module)s: %(message)s')

fh = logging.FileHandler(os.path.join(log_dir, 'smlog'))
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)


mylogger = logging.getLogger('MyLogger')
mylogger.setLevel(logging.DEBUG)
mylogger.addHandler(fh)



debug = mylogger.debug
info = mylogger.info
warning = mylogger.warning
error = mylogger.error
critical = mylogger.critical

