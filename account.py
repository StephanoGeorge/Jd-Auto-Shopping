import logging
import re
import time
from random import random

import glb
import requests


class Account:
    def __init__(self, id, _config):
        self.id = id
        self.config = _config['config']
        self.sess = requests.Session()
        self.sess.cookies.update(_config['cookies'])
        self.sess.headers.update(glb.reqHeaders)
        self.isBuying = False

    # TODO: 使用 APP 的数据保持登录
    def checkLogin(self):
        return glb.request(
            '检测登录', glb.GET, 'https://passport.jd.com/loginservice.aspx?method=Login',
            headers={'Referer': 'https://www.jd.com/'},
            sess=self.sess, logLvl={glb.successLogLvl: logging.DEBUG}, timeout=5)

    def buy(self, itemId):
        while self.isBuying:
            if not glb.items[itemId]:
                return
        self.isBuying = True
        success = False
        try:
            # TODO: 查看是否限购
            # 添加到购物车
            if glb.request(
                    '添加到购物车({})'.format(', '.join((self.id, itemId))), glb.GET, 'https://cart.jd.com/gate.action',
                    params={'pid': itemId, 'pcount': 1, 'ptype': 1},
                    sess=self.sess, redirect=False,
                    logLvl={glb.defaultLogLvl: logging.ERROR,
                            glb.redirectLogLvl: logging.DEBUG}, timeout=3) is None:
                return

            def getOrderInfoCheck(_resp, args):
                if re.search('showCheckCode" value="(.+)"', _resp.text).group(1) == 'true':
                    logging.warning('结算({}) 需要通过图形验证码'.format(', '.join((args[0].id, itemId))))
                time.sleep(1)
                return True

            # 结算
            resp = glb.request(
                '结算({})'.format(', '.join((self.id, itemId))), glb.GET,
                'https://trade.jd.com/shopping/order/getOrderInfo.action',
                sess=self.sess, checkFuc=getOrderInfoCheck, args=[self],
                logLvl={glb.defaultLogLvl: logging.ERROR}, timeout=3)
            if resp is None:
                return

            self.config['riskControl'] = re.search('riskControl" value="(.+?)"', resp.text).group(1)
            logging.info('riskControl: {}'.format(self.config['riskControl']))

            def submitOrderCheck(_resp, args):
                if _resp.json()['resultCode'] in (60123, 600157, 600158):
                    logging.error('提交订单({}) 失败({})'.format(', '.join((args[0].id, itemId)), _resp.json['message']))
                    return False
                elif _resp.json()['resultCode'] is 60017:
                    logging.error('提交订单({}) 请求过于频繁'.format(', '.join((args[0].id, itemId))))
                    time.sleep(5)
                    return True
                elif _resp.json()['success'] is True:
                    logging.error('提交订单({}) 成功'.format(', '.join((args[0].id, itemId))))
                    args[1] = True
                    return False

            # 提交订单
            if glb.request(
                    '提交订单({})'.format(', '.join((self.id, itemId))), glb.POST,
                    'https://trade.jd.com/shopping/order/submitOrder.action',
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
                    checkFuc=submitOrderCheck, args=[self, success],
                    logLvl={glb.defaultLogLvl: logging.ERROR}, timeout=3) is None:
                return
            # 失败后删除商品
        finally:
            if not success:
                glb.request('remove from cart ({})'.format(', '.join((itemId, self.id))), glb.POST,
                            'https://cart.jd.com/removeSkuFromCart.action',
                            data={'venderId': '8888', 'pid': itemId, 'ptype': '1', 'packId': '0',
                                  'targetId': '0', 't': '0', 'outSkus': '', 'random': '0.3794799431176733',
                                  'locationId': glb.config['area']},
                            headers={'Content-Type': 'application/x-www-form-urlencoded',
                                     'Origin': 'https://cart.jd.com',
                                     'Referer': 'https://cart.jd.com/cart.action'},
                            sess=self.sess, timeout=5)
            self.isBuying = False
