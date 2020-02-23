import logging
from json import JSONDecodeError

import time

from threading import Thread

import account
import glb

isInStockApiParams = []
_count = 100
_currIndex = 0
while True:
    # 分割商品列表
    _currItems = list(glb.config['items'].keys())[_currIndex:_currIndex + _count]
    if len(_currItems) != 0:
        isInStockApiParams.append({
            'skuIds': ','.join([itemId for itemId in _currItems]),
            'area': glb.accountList[0].config['areaId'],  # 使用第1个账户的
            'type': 'getstocks'})
        _currIndex += _count
        continue
    else:
        break


def checkLogin():
    while True:
        for _account in glb.accountList:
            resp = _account.checkLogin()
            if resp is None:
                continue
            if not resp.json()['Identity']['IsAuthenticated']:
                logging.error('{} 未登录'.format(_account.id))
        time.sleep(60)


def monitor():
    logging.info('### 检查是否为抢购商品 ###')
    _checkSnappingUp()
    logging.info('### 开始监控库存 ###')
    for isInStockApiParam in isInStockApiParams:
        Thread(target=_monitor, args=(isInStockApiParam,)).start()
    Thread(target=checkSnappingUp).start()


def checkSnappingUp():
    while True:
        _checkSnappingUp()


def _checkSnappingUp():
    for itemId in glb.runTimeItems.keys():
        resp = glb.request(
            '检查是否为抢购商品', None, glb.GET, 'https://yushou.jd.com/youshouinfo.action',
            params={'sku': itemId},
            headers={'referer': 'https://item.jd.com/{}.html'.format(itemId),
                     'cookie': None},
            logLvl={glb.successLogLvl: logging.DEBUG,  # 请求成功的日志等级
                    glb.timeoutLogLvl: logging.DEBUG,  # 请求超时的日志等级
                    glb.tooManyFailureLogLvl: logging.DEBUG},  # 过多失败的日志等级
            timeout=3)
        if resp is not None and resp.text != '{"error":"pss info is null"}':
            if not glb.runTimeItems[itemId][glb.isSnappingUp]:
                logging.warning('{} 是抢购商品, 不自动购买'.format(itemId))
                glb.runTimeItems[itemId][glb.isSnappingUp] = True
        elif glb.runTimeItems[itemId][glb.isSnappingUp]:
            logging.warning('{} 不是抢购商品, 会自动购买'.format(itemId))
            glb.runTimeItems[itemId][glb.isSnappingUp] = False


def _monitor(isInStockApiParam):
    while True:
        resp = glb.request('监控库存', None, glb.GET, 'https://c0.3.cn/stocks',
                           params=isInStockApiParam, headers={'cookie': None},
                           logLvl={glb.successLogLvl: logging.DEBUG,  # 请求成功的日志等级
                                   glb.timeoutLogLvl: logging.DEBUG,  # 请求超时的日志等级
                                   glb.tooManyFailureLogLvl: logging.DEBUG},  # 过多失败的日志等级
                           timeout=1.5)
        if resp is not None:
            try:
                for itemId, value in resp.json().items():
                    if value['skuState'] == 0 or value['StockState'] not in (33, 40):
                        glb.runTimeItems[itemId][glb.isInStock] = False
                    else:
                        glb.runTimeItems[itemId][glb.isInStock] = True
                        if canBuy(itemId):
                            Thread(target=buy, args=(itemId,)).start()
            except JSONDecodeError:
                continue


def canBuy(itemId):
    item = glb.runTimeItems[itemId]
    if item[glb.isInStock] and not item[glb.isSnappingUp]:
        logging.warning('{} 有货 且不是抢购商品'.format(itemId))
        return True
    else:
        return False


def buy(itemId):
    idsOfAccountsWantToBuy = glb.config['items'][itemId]
    if len(idsOfAccountsWantToBuy) == 0:
        for account in glb.accountList:
            Thread(target=account.buy, args=(itemId,)).start()
    else:
        for _id in idsOfAccountsWantToBuy:
            Thread(target=glb.accountDict[_id].buy, args=(itemId,)).start()
