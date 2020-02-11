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
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3835.0 Safari/537.36',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Cache-Control': 'no-cache',
    'TE': 'Trailers'
}

GET = 'GET'
POST = 'POST'

with open(configFileName) as file:
    config = json.load(file)

accountList: List[account.Account] = []
for _phoneNumber, _config in config['accounts'].items():
    accountList.append(account.Account(_phoneNumber, _config))


def saveConfig():
    with open(configFileName, 'w') as _file:
        for _account in accountList:
            config['accounts'][_account.phoneNumber]['cookies'] = _account.sess.cookies.get_dict()
        json.dump(config, _file)


atexit.register(saveConfig)

_currAccountIndex = 0


def requestUntilSuccess(
        actionName, method, url, params=None, data=None, headers=None, cookies=None,
        sess: requests.Session = None,
        checkFun=lambda _resp: _resp.status_code == 200, redirect=True,
        logLvl=logging.WARNING, timeout=2):
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
                headers={**(headers if headers is not None else {}),
                         'Host': re.search('https?://(.*?)(/|$)', url).group(1)},
                cookies=cookies,
                timeout=timeout,
                allow_redirects=False)
            if 'Location' in resp.headers:
                logging.log(logLvl, '从 {} 重定向至 {}'.format(url, resp.headers['Location']))
                if redirect:
                    url = resp.headers['Location']
                    # headers['Referer'] =
                    continue
                else:
                    return resp
            if 400 <= resp.status_code < 500:
                logging.log(logLvl, '\n\t'.join(('{} 返回客户端错误'.format(actionName), str(resp.status_code))))
                attemptTimes -= 3
                time.sleep(sleepTime)
                continue
            if not checkFun(resp):
                logging.log(logLvl, '\n\t'.join(('{} 未通过检查'.format(actionName), str(resp.status_code),
                                                 str(resp.headers), resp.text)))
                attemptTimes -= 3
                time.sleep(sleepTime)
                continue
            logging.log(logLvl - 10, '{} 成功'.format(actionName))
            return resp
        except Timeout:
            logging.log(logLvl, '{} 超时'.format(actionName))
            continue
        except TooManyRedirects:
            logging.log(logLvl, '{} 重定向过多'.format(actionName))
            return None
        except (Exception, IOError, socket.timeout) as e:
            if resp is None:
                logging.log(logLvl, '{} 失败, 无 Response'.format(actionName))
            else:
                logging.log(logLvl, '\n\t'.join(('{} 失败'.format(actionName), str(resp.status_code),
                                                 str(resp.headers), resp.text)))
            logging.exception(e)
            continue
    else:
        logging.log(logLvl, '{} 超过尝试次数'.format(actionName))
        return None
