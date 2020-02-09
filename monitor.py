import json
import logging
import threading
from threading import Thread

import time
from requests import Timeout

from seleniumwire import webdriver

import globals
from globals import *

isInStockApiParams = {
    'areaRequest': {'provinceId': config['provinceId'],
                    'cityId': config['cityId'],
                    'countyId': config['countyId'],
                    'townId': config['townId']},
    'coordnateRequest': {
        'latitude': config['latitude'],
        'longtitude': config['longtitude']},
    'skuNumList': [{'skuId': item, 'num': '1'} for item, ok in config['items'].items() if ok]
}


def monitor():
    while True:
        # startTime = time.time()
        # logging.warning('使用账号: {}'.format(_account.config['phoneNumber']))
        # while True:
        resp = requestUntilSuccess(GET, 'https://trade.jd.com/api/v1/batch/stock',
                                   _headers={'Content-Type': 'application/json; charset=utf-8',
                                             'Origin': 'https://trade.jd.com',
                                             # 'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
                                             'TE': 'Trailers'},
                                   data=isInStockApiParams,
                                   actionName='监控库存',
                                   checkFun=lambda _resp: True,
                                   timeout=1,
                                   sleepTime=0.3,
                                   attemptTimes=3)
        if resp is None:
            continue
        if resp.text == '{"error":"NotLogin"}':
            logging.exception('登录失效')
        if 'text/html' in resp.headers['Content-Type']:
            removeItems()
            continue
        for itemId, value in resp.json().items():
            if '有货' in value['status']:
                logging.warning('{} 有货'.format(itemId))
                # Thread(target=buy, args=itemId).start()
                buy(itemId)


def buy(itemId):
    for _account in accountList:
        Thread(target=_account.buy, args=itemId).start()


def removeItems():
    logging.warning('检查下架')
    print(isInStockApiParams['skuNumList'])
    for item in isInStockApiParams['skuNumList']:
        itemId = item['skuId']
        resp = requestUntilSuccess(GET, 'https://item.jd.com/{}.html'.format(itemId),
                                   actionName='检查下架')
        if '该商品已下柜' in resp.text:
            logging.warning('{} 已下架'.format(itemId))
            config['items'][itemId] = False
            isInStockApiParams['skuNumList'].remove(item)

        # def getStockParams():
        #     for _account in globals.accountList:
        #         if _account.hasLoggedIn:
        #             _account.driver.get('https://trade.jd.com/shopping/order/getOrderInfo.action')
        #             for request in _account.driver.requests:
        #                 if request.path == 'https://trade.jd.com/api/v1/batch/stock':
        #                     print(request.body)
        #                 # if request.response:
        #                 #     print(
        #                 #         request.path,
        #                 #         request.response.body,
        #                 #     )
