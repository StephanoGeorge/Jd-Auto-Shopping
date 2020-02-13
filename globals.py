import json
import logging
import re
import socket

import atexit
import time
from typing import List
import requests
from requests import Timeout, TooManyRedirects

import account

configFileName = './config.json'
headers = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'accept-language': 'zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2',
    'accept-encoding': 'gzip, deflate',
    'DNT': '1',
    'connection': 'keep-alive',
    'Pragma': 'no-cache',
    'cache-control': 'no-cache',
    'TE': 'Trailers'
}

GET = 'GET'
POST = 'POST'

with open(configFileName) as file:
    config = json.load(file)
accountList: List[account.Account] = []
for _id, _config in config['accounts'].items():
    # remove unASCII char
    for _key, _value in tuple(_config['cookies'].items()):
        if re.search(r'[^\u0000-\u007F]', _value) is not None:
            del _config['cookies'][_key]
    accountList.append(account.Account(_id, _config))


def saveConfig():
    with open(configFileName, 'w') as _file:
        for _account in accountList:
            config['accounts'][_account.id]['cookies'] = _account.sess.cookies.get_dict()
        json.dump(config, _file)


atexit.register(saveConfig)

_currAccountIndex = 0
defaultLogLvl = 0
successLogLvl = 1
timeoutLogLvl = 2
TooManyFailureLogLvl = 3


def request(
        actionName, method, url, params=None, data=None, headers={}, cookies=None,
        sess: requests.Session = None,
        checkFun=lambda _resp: _resp.status_code == 200, redirect=True,
        logLvl={}, timeout=2):
    logLvl = {defaultLogLvl: logging.WARNING,
              successLogLvl: logging.INFO,
              timeoutLogLvl: logging.WARNING,
              TooManyFailureLogLvl: logging.WARNING,
              **logLvl}
    sleepTime = 0
    attemptTimes = 10
    while attemptTimes > 0:
        attemptTimes -= 1
        sleepTime += 0.5
        resp = None
        try:
            # 使用账户列表中的 session
            if sess is None:
                global _currAccountIndex
                sess = accountList[_currAccountIndex].sess
                if _currAccountIndex == len(accountList) - 1:
                    _currAccountIndex = 0
                else:
                    _currAccountIndex += 1
            resp = sess.request(
                method, url, params, data,
                headers={'Host': re.search('https?://(.*?)(/|$)', url).group(1),
                         **headers},
                cookies=cookies,
                timeout=timeout,
                allow_redirects=False)
            if 'Location' in resp.headers:
                logging.log(logLvl[defaultLogLvl] - 10, '从 {} 重定向至 {}'.format(url, resp.headers['Location']))
                if redirect:
                    url = resp.headers['location']
                    # headers['Referer'] =
                    continue
                else:
                    return resp
            if 400 <= resp.status_code < 500:
                logging.log(logLvl[defaultLogLvl],
                            '\n\t'.join(('{} 发生客户端错误'.format(actionName), str(resp.status_code))))
                attemptTimes -= 3
                time.sleep(sleepTime)
                continue
            if not checkFun(resp):
                logging.log(logLvl[defaultLogLvl], '\n\t'.join(('{} 未通过检查'.format(actionName), str(resp.status_code),
                                                                str(resp.headers), resp.text)))
                attemptTimes -= 3
                time.sleep(sleepTime)
                continue
            logging.log(logLvl[successLogLvl], '{} 成功'.format(actionName))
            return resp
        except Timeout:
            logging.log(logLvl[timeoutLogLvl], '{} 超时'.format(actionName))
            continue
        except TooManyRedirects:
            logging.log(logLvl[defaultLogLvl], '{} 重定向次数过多'.format(actionName))
            return None
        except Exception as e:
            if resp is None:
                logging.log(logLvl[defaultLogLvl], '{} 失败, 无 Response'.format(actionName))
            else:
                logging.log(logLvl[defaultLogLvl], '\n\t'.join(('{} 失败'.format(actionName), str(resp.status_code),
                                                                str(resp.headers), resp.text)))
            logging.exception(e)
            continue
    else:
        logging.log(logLvl[TooManyFailureLogLvl], '{} 失败次数过多'.format(actionName))
        return None
