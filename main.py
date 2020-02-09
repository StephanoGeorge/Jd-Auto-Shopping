import logging
from threading import Thread

import globals
import cookies
import login
import monitor
import account

logging.basicConfig(format='%(asctime)s %(message)s')

login.login()
# Thread(target=login.login).start()
Thread(target=monitor.monitor).start()


# Thread(target=refreshPage).start()
# Thread(target=monitor).start()
# for i in accountList:
#     login
#     loggedInAccountList.append()



