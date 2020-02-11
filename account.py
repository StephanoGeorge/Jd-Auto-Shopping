import logging
import re
from random import random

import globals
import requests


class Account:
    def __init__(self, phoneNumber, _config):
        self.phoneNumber = phoneNumber
        self.config = _config['config']
        self.sess = requests.Session()
        self.sess.cookies.update(_config['cookies'])
        self.sess.headers.update(globals.headers)
        self.isBuying = False
        self.alreadyPurchased = []

    def checkLogin(self):
        return globals.requestUntilSuccess(
            '检测登录', globals.GET,
            'https://passport.jd.com/loginservice.aspx?method=Login',
            headers={'Referer': 'https://www.jd.com/'},
            sess=self.sess,
            sleepTime=0,
            attemptTimes=5).json()['Identity']['IsAuthenticated']

    def buy(self, itemId):
        if itemId in self.alreadyPurchased:
            return
        while self.isBuying:
            pass
        self.isBuying = True
        try:
            # 添加到购物车
            if globals.requestUntilSuccess(
                    '添加到购物车', globals.GET, 'https://cart.jd.com/gate.action',
                    params={'pid': itemId, 'pcount': int(random() * 5) + 1, 'ptype': 1},
                    sess=self.sess,
                    logLvl=logging.ERROR,
                    timeout=3,
                    sleepTime=0.5,
                    attemptTimes=10) is None:
                return

            # 结算
            resp = globals.requestUntilSuccess(
                '结算', globals.GET, 'https://trade.jd.com/shopping/order/getOrderInfo.action',
                sess=self.sess,
                timeout=3,
                sleepTime=0.5,
                attemptTimes=30)
            if resp is None:
                return
            self.config['riskControl'] = re.search('riskControl" value="(.+?)"', resp.text).group(1)

            # 提交订单
            if globals.requestUntilSuccess(
                    '提交订单', globals.POST, 'https://trade.jd.com/shopping/order/submitOrder.action',
                    headers={'Origin': 'https://trade.jd.com',
                             'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action'},
                    data={
                        'overseaPurchaseCookies': '',
                        'vendorRemarks': '[]',
                        'submitOrderParam.sopNotPutInvoice': 'false',
                        'submitOrderParam.trackID': 'TestTrackId',
                        'submitOrderParam.ignorePriceChange': '0',
                        'submitOrderParam.btSupport': '0',
                        # https://gia.jd.com/fcf.html
                        'submitOrderParam.eid': self.config['eid'],
                        'submitOrderParam.fp': self.config['fp'],
                        'riskControl': self.config['riskControl'],
                        'submitOrderParam.jxj': 1,
                        'submitOrderParam.trackId': self.config['trackId'],
                        'submitOrderParam.isBestCoupon': 1,  #
                        'submitOrderParam.needCheck': 1,  #
                    },
                    checkFun=lambda resp: resp.json()['success'],
                    logLvl=logging.ERROR,
                    timeout=3,
                    sleepTime=0.5,
                    attemptTimes=5) is None:
                return
            self.alreadyPurchased.append(itemId)
        finally:
            self.isBuying = False
