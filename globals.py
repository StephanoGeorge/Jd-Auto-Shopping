import json
import logging
import os
import re

import atexit
import time
from typing import List
import requests
from requests import Timeout, TooManyRedirects

import account

cookieFileName = './cookies.json'
configFileName = './config.json'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
}
GET = 'GET'
POST = 'POST'


def saveConfig():
    with open(configFileName, 'w') as _file:
        for _account in accountList:
            config['accounts'][_account.phoneNumber]['cookies'] = _account.sess.cookies.get_dict()
        json.dump(config, _file)


with open('./config.json') as file:
    config = json.load(file)
# with open(cookieFileName) as _file:
#     _cookies = json.load(_file)

accountList: List[account.Account] = []
for _phoneNumber, _config in config['accounts'].items():
    accountList.append(account.Account(_phoneNumber, _config))

atexit.register(saveConfig)

_currAccountIndex = 0


def requestUntilSuccess(method, url, params=None, data=None, _headers=None, cookies=None, sess: requests.Session = None,
                        actionName=None, checkFun=lambda _resp: _resp.status_code == 200,
                        successLogMsgFun=lambda _resp: None,
                        timeout=2, sleepTime=0.5, attemptTimes=5):
    _sleepTime = 0
    _attemptTimes = attemptTimes
    while attemptTimes > 0:
        attemptTimes -= 1
        _sleepTime += sleepTime
        resp = None
        try:
            if sess is None:
                global _currAccountIndex
                _sess = accountList[_currAccountIndex].sess
                if _currAccountIndex == len(accountList) - 1:
                    _currAccountIndex = 0
                else:
                    _currAccountIndex += 1
            else:
                _sess = sess
            resp = _sess.request(method, url, params, data,
                                 headers={**(_headers if _headers is not None else {}),
                                          'Host': re.search('https?://(.*?)(/|$)', url).group(1),
                                          # 'Referer': referer
                                          },
                                 cookies=cookies,
                                 timeout=timeout,
                                 allow_redirects=False)
            # print(resp.request.headers)
            # print(resp.request.data)
            # logging.warning('\n'.join((url, str(resp.status_code))))
            if 300 <= resp.status_code < 400:
                logging.warning('从 {} 重定向至 {}'.format(url, resp.headers['Location']))
                url = resp.headers['Location']
                # headers['Referer'] =
                continue
            if not checkFun(resp):
                raise Exception()
            successLogMsg = successLogMsgFun(resp)
            if successLogMsg is not None:
                logging.warning(', '.join(('{} 成功'.format(actionName), successLogMsg)))
        except Timeout:
            logging.warning('{} 超时'.format(actionName))
            continue
        except TooManyRedirects:
            logging.warning('{} 重定向过多'.format(actionName))
            return None
        except Exception as e:
            if resp is None:
                logging.warning('\n'.join(('{} 失败'.format(actionName), url)))
            else:
                logging.warning(
                    '\n'.join(('{} 失败'.format(actionName), url, str(resp.status_code), str(resp.headers), resp.text)))
            logging.exception(e)
            time.sleep(_sleepTime)
            continue
        return resp
    else:
        logging.warning('{} 超过尝试次数 ({})'.format(actionName, _attemptTimes))
        return None
