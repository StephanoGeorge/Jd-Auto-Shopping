import logging
import time
from threading import Thread

import globals

isInStockApiParams = {
    'skuIds': ','.join([itemId for itemId, _ in globals.config['items'].items()]),
    'area': globals.config['area'],
    'type': 'getstocks',
}


#  Test
def keepLogin():
    while True:
        for _account in globals.accountList:
            if _account.checkLogin():
                logging.debug('{} 已登录'.format(_account.phoneNumber))
            else:
                logging.error('{} 未登录'.format(_account.phoneNumber))
        else:
            logging.debug('所有账户都已登录')
        time.sleep(60 * 20)


def monitor():
    logging.debug('开始监控库存')
    while True:
        # startTime = time.time()
        # logging.warning('使用账号: {}'.format(_account.config['phoneNumber']))
        # while True:
        resp = globals.requestUntilSuccess(
            '监控库存', globals.GET, 'https://c0.3.cn/stocks',
            params=isInStockApiParams,
            headers={'Cookie': None},
            logLvl=logging.DEBUG,
            timeout=1.5,
            sleepTime=0,
            attemptTimes=3)
        if resp is None:
            continue
        for itemId, value in resp.json().items():
            if value['skuState'] == 0:
                # isInStockApiParams['skuIds'] = re.sub('{},?'.format(itemId), '', isInStockApiParams['skuIds'])
                globals.config['items'][itemId] = False
                continue
            if value['StockState'] in (33, 40):
                logging.warning('{} 有货'.format(itemId))
                # Thread(target=buy, args=itemId).start()
                buy(itemId)


def buy(itemId):
    for _account in globals.accountList:
        Thread(target=_account.buy, args=itemId, daemon=True).start()
