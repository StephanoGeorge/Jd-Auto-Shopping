import logging

import globals
import requests


class Account:
    def __init__(self, phoneNumber, _config):
        self.phoneNumber = phoneNumber
        self.config = _config['config']
        self.sess = requests.Session()
        self.sess.cookies.update(_config['cookies'])
        self.sess.headers.update(globals.headers)

    def checkLogin(self):
        return globals.requestUntilSuccess('检测登录', globals.GET,
                                           'https://passport.jd.com/loginservice.aspx?method=Login',
                                           headers={'Referer': 'https://www.jd.com/'},
                                           sess=self.sess,
                                           sleepTime=0,
                                           attemptTimes=5).json()['Identity']['IsAuthenticated']

    def buy(self, itemId):
        # 添加到购物车
        if globals.requestUntilSuccess('添加到购物车', globals.GET, 'https://cart.jd.com/gate.action',
                                       params={'pid': itemId, 'pcount': 1, 'ptype': 1},
                                       sess=self.sess,
                                       logLvl=logging.ERROR,
                                       timeout=3,
                                       sleepTime=0.5,
                                       attemptTimes=10) is None:
            return
        # 结算
        # if globals.requestUntilSuccess(globals.GET, 'https://trade.jd.com/shopping/order/getOrderInfo.action',
        #                                sess=self.sess,
        #                                actionName='结算',
        #                                successLogMsgFun=lambda resp: self.phoneNumber,
        #                                timeout=3,
        #                                sleepTime=0.5,
        #                                attemptTimes=10) is None:
        #     return
        # 提交订单
        if globals.requestUntilSuccess('提交订单', globals.POST, 'https://trade.jd.com/shopping/order/submitOrder.action',
                                       headers={
                                           'Origin': 'https://trade.jd.com',
                                           'Referer': 'https://trade.jd.com/shopping/order/getOrderInfo.action'},
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
                                       },
                                       checkFun=lambda resp: resp.json()['success'],
                                       logLvl=logging.ERROR,
                                       timeout=3,
                                       sleepTime=0.5,
                                       attemptTimes=10) is None:
            return

    # def loadAccountPage(self):
    #     globals.requestUntilSuccess(globals.GET, 'https://api.m.jd.com/api?appid=pc_home_page&functionId=getHomeWalletInfo&loginType=3',
    #                                 headers={'Referer': 'https://home.jd.com/'},
    #                                 sess=self.sess,
    #                                 actionName='加载账户页面',
    #                                 timeout=5,
    #                                 sleepTime=5)
