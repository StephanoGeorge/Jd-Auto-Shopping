import logging
import os

from threading import Thread

import globals

isInStockApiParams = []
_count = 100
_currIndex = 0
while True:
    _currItems = list(globals.config['items'].keys())[_currIndex:_currIndex + _count]
    if len(_currItems) != 0:
        isInStockApiParams.append({
            'skuIds': ','.join([itemId for itemId in _currItems]),
            'area': globals.config['area'],
            'type': 'getstocks'})
        _currIndex += _count
        continue
    else:
        break


def checkLogin():
    for _account in globals.accountList:
        if _account.checkLogin():
            logging.debug('{} 已登录'.format(_account.phoneNumber))
        else:
            logging.error('{} 未登录'.format(_account.phoneNumber))
            os._exit()
    else:
        logging.debug('所有账户都已登录')


def monitor():
    logging.debug('开始监控库存')
    while True:
        for isInStockApiParam in isInStockApiParams:
            resp = globals.requestUntilSuccess(
                '监控库存', globals.GET, 'https://c0.3.cn/stocks',
                params=isInStockApiParam,
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
        Thread(target=_account.buy(itemId), daemon=True).start()
