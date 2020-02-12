import logging
from threading import Thread

import monitor
# 设置日志
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
# 检查登录
Thread(target=monitor.checkLogin).start()
# 监控
monitor.monitor()
