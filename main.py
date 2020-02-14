from threading import Thread

import monitor
# 检查登录
Thread(target=monitor.checkLogin).start()
# 监控
monitor.monitor()
