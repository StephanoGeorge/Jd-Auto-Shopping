import logging
from threading import Thread

import monitor
# 设置日志
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
# 保持登录
monitor.checkLogin()
# 监控
monitor.monitor()
