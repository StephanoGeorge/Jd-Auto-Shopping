import logging
import os
import re
import time
from random import random

import glb
import requests


def canBuy(itemId):
    item = glb.runTimeItems[itemId]
    return item[glb.isInStock] and not item[glb.isSnappingUp]


class Account:
    def __init__(self, id, config):
        self.id = id
        self.config = config['config']
        self.sess = requests.Session()
        self.sess.cookies.update(config['cookies'])
        self.sess.headers.update(glb.reqHeaders)
        self.isBuying = False

    def checkLogin(self):
        return glb.request(
            '检测登录', self.sess, glb.GET, 'https://passport.jd.com/loginservice.aspx?method=Login',
            headers={'Referer': 'https://www.jd.com/'},
            logLvl={glb.successLogLvl: logging.DEBUG,
                    glb.timeoutLogLvl: logging.DEBUG}, timeout=5)

    def buy(self, itemId):
        while self.isBuying:
            if not canBuy(itemId):
                return
        self.isBuying = True
        success = [False]
        logging.warning('开始购买 ({})'.format(', '.join((self.id, itemId))))
        try:
            # 添加到购物车
            if glb.request(
                    '添加到购物车 ({})'.format(', '.join((self.id, itemId))), self.sess, glb.GET,
                    'https://cart.jd.com/gate.action', params={'pid': itemId, 'pcount': 1, 'ptype': 1},
                    redirect=False, logLvl={glb.defaultLogLvl: logging.ERROR,
                                            glb.redirectLogLvl: logging.DEBUG}, timeout=3) is None:
                return
            logging.warning('添加到购物车 ({}) 成功'.format(', '.join((self.id, itemId))))

            def getOrderInfoCheck(_resp, args):
                if re.search('showCheckCode" value="(.+)"', _resp.text).group(1) == 'true':
                    logging.warning('结算 ({}) 需要通过图形验证码'.format(', '.join((args[0].id, args[1]))))
                    time.sleep(1)
                    return True
                return False

            # 结算
            resp = glb.request(
                '结算 ({})'.format(', '.join((self.id, itemId))), self.sess, glb.GET,
                'https://trade.jd.com/shopping/order/getOrderInfo.action',
                checkFuc=getOrderInfoCheck, args=(self, itemId),
                redirect=False, logLvl={glb.defaultLogLvl: logging.ERROR}, timeout=3)
            if resp is None:
                return

            riskControl = re.search('riskControl" value="(.+?)"', resp.text).group(1)

            def submitOrderCheck(_resp, args):
                if _resp.json()['resultCode'] in (60123, 600157):
                    logging.error('提交订单 ({}) 失败 (message: {})'.format(
                        ', '.join((args[0].id, args[1])), _resp.json()['message']))
                    return False
                elif _resp.json()['resultCode'] is 600158:
                    logging.error('提交订单 ({}) 失败 (无货)'.format(', '.join((args[0].id, args[1]))))
                    glb.runTimeItems[args[1]][glb.isInStock] = False
                    return False
                elif _resp.json()['resultCode'] is 60017:
                    logging.error('提交订单 ({}) 失败 (请求过于频繁), 睡眠5s'.format(', '.join((args[0].id, args[1]))))
                    time.sleep(5)
                    return True
                elif _resp.json()['success'] is True:
                    logging.error('\n\n\n提交订单 ({}) 成功!!!!!!!!!!!!!!!!!!!\n\n\n'.format(
                        ', '.join((args[0].id, args[1]))))
                    args[2][0] = True
                    return False
                else:
                    logging.error('提交订单 ({}) 失败 ({})'.format(
                        ', '.join((args[0].id, args[1])), _resp.json()))
                    return False

            # 提交订单
            if glb.request(
                    '提交订单 ({})'.format(', '.join((self.id, itemId))), self.sess, glb.POST,
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
                        'submitOrderParam.eid': self.config['eid'],  # https://gia.jd.com/fcf.html
                        'submitOrderParam.fp': self.config['fp'],
                        'riskControl': riskControl,
                        'submitOrderParam.jxj': 1,
                        'submitOrderParam.trackId': self.config['trackId'],
                        # 'submitOrderParam.isBestCoupon': 1,  #
                        # 'submitOrderParam.needCheck': 1,  #
                    },
                    checkFuc=submitOrderCheck, args=(self, itemId, success),
                    logLvl={glb.defaultLogLvl: logging.ERROR}, timeout=3) is None:
                return
        finally:
            # 失败后删除商品
            if not success[0]:
                glb.request(
                    '从购物车删除 ({})'.format(', '.join((self.id, itemId))), self.sess, glb.POST,
                    'https://cart.jd.com/removeSkuFromCart.action',
                    data={'venderId': '8888', 'pid': itemId, 'ptype': '1', 'packId': '0',
                          'targetId': '0', 't': '0', 'outSkus': '', 'random': '0.3794799431176733',
                          'locationId': self.config['areaId']},
                    headers={'Content-Type': 'application/x-www-form-urlencoded',
                             'Origin': 'https://cart.jd.com',
                             'Referer': 'https://cart.jd.com/cart.action'},
                    timeout=5)
            self.isBuying = False
