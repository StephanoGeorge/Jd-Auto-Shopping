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

    def checkLogin(self):
        return globals.requestUntilSuccess(
            '检测登录', globals.GET,
            'https://passport.jd.com/loginservice.aspx?method=Login',
            headers={'Referer': 'https://www.jd.com/'},
            sess=self.sess).json()['Identity']['IsAuthenticated']

    def buy(self, itemId):
        if self.isBuying:
            return
        self.isBuying = True
        try:
            # 添加到购物车
            if globals.requestUntilSuccess(
                    '添加到购物车', globals.GET, 'https://cart.jd.com/gate.action',
                    params={'pid': itemId, 'pcount': int(random() * 5) + 1, 'ptype': 1},
                    sess=self.sess, logLvl=logging.ERROR, timeout=3) is None:
                return

            # 结算
            resp = globals.requestUntilSuccess(
                '结算', globals.GET, 'https://trade.jd.com/shopping/order/getOrderInfo.action',
                sess=self.sess, timeout=3)
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
                        'submitOrderParam.eid': self.config['eid'],  # 几乎不变
                        'submitOrderParam.fp': self.config['fp'],  # 几乎不变
                        'riskControl': self.config['riskControl'],
                        'submitOrderParam.jxj': 1,
                        'submitOrderParam.trackId': self.config['trackId'],
                        'submitOrderParam.isBestCoupon': 1,  #
                        'submitOrderParam.needCheck': 1,  #
                    },
                    checkFun=lambda _resp: _resp.json()['success'],
                    logLvl=logging.ERROR,
                    timeout=3) is None:
                return
        finally:
            self.isBuying = False
