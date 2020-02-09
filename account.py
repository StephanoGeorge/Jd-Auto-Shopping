import requests
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options

import globals
from globals import *


class Account:
    def __init__(self, phoneNumber, _config):
        self.phoneNumber = phoneNumber
        self.config = _config
        self.sess = requests.Session()
        self.sess.cookies.update(self.config['cookies'])
        self.sess.headers.update(globals.headers)

        # self.cookiesLock = threading.Lock()

        # self._options = Options()
        # self._options.add_argument(
        #     'user-agent=Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0')
        # # self._options.add_experimental_option('prefs', {
        # #     # 禁止加载图片
        # #     # 'profile.managed_default_content_settings.images': 2,
        # #     # 禁止加载 CSS
        # #     # 'permissions.default.stylesheet': 2
        # # })
        # self.driver = webdriver.Chrome(chrome_options=self._options)

        self.hasLoggedIn = False

    def buy(self, itemId):
        # 添加到购物车
        globals.requestUntilSuccess(self.sess,
                                    requests.Request('GET', url='https://cart.jd.com/gate.action',
                                                     params={'pid': itemId, 'pcount': 1, 'ptype': 1}),
                                    checkFun=lambda resp: ('已成功加入购物车' in resp.text),
                                    actionName='添加到购物车',
                                    timeout=3,
                                    sleepTime=0.5,
                                    attemptTimes=10)
        # 结算
        globals.requestUntilSuccess(self.sess,
                                    requests.Request('GET',
                                                     url='https://trade.jd.com/shopping/order/getOrderInfo.action'),
                                    actionName='结算',
                                    timeout=3,
                                    sleepTime=0.5,
                                    attemptTimes=10)
        # 提交订单
        globals.requestUntilSuccess(self.sess,
                                    requests.Request('POST',
                                                     url='https://trade.jd.com/shopping/order/submitOrder.action',
                                                     params={'pid': itemId, 'pcount': 1, 'ptype': 1},
                                                     headers={
                                                         'Host': 'trade.jd.com',
                                                         'Origin': 'https://trade.jd.com',
                                                         'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action',
                                                     },
                                                     data={
                                                         'overseaPurchaseCookies': '',
                                                         'vendorRemarks': '[]',
                                                         'submitOrderParam.sopNotPutInvoice': 'false',
                                                         'submitOrderParam.trackID': 'TestTrackId',
                                                         'submitOrderParam.ignorePriceChange': '0',
                                                         'submitOrderParam.btSupport': '0',
                                                         'submitOrderParam.eid': self.config['eid'],
                                                         'submitOrderParam.fp': self.config['fp'],
                                                         'riskControl': self.config['riskControl'],
                                                         'submitOrderParam.jxj': 1,
                                                         'submitOrderParam.trackId': self.config['trackId'],
                                                         # 'submitOrderParam.isBestCoupon': 1,
                                                         # 'submitOrderParam.needCheck': 1,
                                                     }),
                                    checkFun=lambda resp: (
                                        resp.json()['success']),
                                    actionName='提交订单',
                                    timeout=3,
                                    sleepTime=0.5,
                                    attemptTimes=10)
