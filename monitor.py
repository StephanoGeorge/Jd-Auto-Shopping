import logging
import time

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
    while True:
        for _account in globals.accountList:
            if _account.checkLogin():
                logging.info('{} 已登录'.format(_account.id))
            else:
                logging.error('{} 未登录'.format(_account.id))
        time.sleep(20 * 60)


def monitor():
    logging.info('开始监控库存')
    for isInStockApiParam in isInStockApiParams:
        Thread(target=_monitor, args=(isInStockApiParam,)).start()


def _monitor(isInStockApiParam):
    while True:
        resp = globals.request('监控库存', globals.GET, 'https://c0.3.cn/stocks',
                               params=isInStockApiParam, headers={'cookie': None},
                               logLvl={globals.successLogLvl: logging.DEBUG,  # 请求成功的日志等级
                                       globals.timeoutLogLvl: logging.DEBUG,  # 请求超时的日志等级
                                       globals.TooManyFailureLogLvl: logging.DEBUG},  # 过多失败的日志等级
                               timeout=1.5)
        if resp is None:
            continue
        for itemId, value in resp.json().items():
            if value['skuState'] == 0:
                # isInStockApiParams['skuIds'] = re.sub('{},?'.format(itemId), '', isInStockApiParams['skuIds'])
                globals.config['items'][itemId] = False
                continue
            if value['StockState'] in (33, 40):
                logging.warning('{} 有货'.format(itemId))
                # Thread(target=buy, args=(itemId,)).start()
                buy(itemId)


def buy(itemId):
    for _account in globals.accountList:
        Thread(target=_account.buy, args=(itemId,)).start()
