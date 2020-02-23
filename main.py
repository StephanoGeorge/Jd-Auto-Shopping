from threading import Thread

import glb
import monitor

# 初始化
glb.init()
monitor.init()
# 检查登录
Thread(target=monitor.checkLogin).start()
# 监控
monitor.monitor()
