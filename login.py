from globals import *


def login():
    for _account in accountList:
        if requestUntilSuccess(GET,
                               'https://passport.jd.com/loginservice.aspx?method=Login',
                               _headers={'Referer': 'https://www.jd.com/'},
                               sess=_account.sess,
                               actionName='检测登录',
                               sleepTime=0,
                               attemptTimes=10).json()['Identity']['IsAuthenticated']:
            logging.warning('已经登录')
            _account.hasLoggedIn = True
            continue
        # _account.driver.get('https://passport.jd.com/new/login.aspx')
        # # while not _account.driver.current_url == 'https://www.jd.com/':
        # #     pass
        # _account.driver.find_element_by_css_selector('.login-tab.login-tab-r').click()
        # _account.driver.find_element_by_id('loginname').send_keys(_account.config['phoneNumber'])
        # _account.driver.find_element_by_id('nloginpwd').send_keys(_account.config['loginPwd'])
        # _account.driver.execute_script("document.getElementById('loginsubmit').click()")
        # _account.driver.find_element_by_id('loginsubmit').click()
        logging.warning('等待登录')
        # while '正在登录' not in _account.driver.find_element_by_id('loginsubmit').text:
        #     pass
        # logging.warning('登录成功')
        # _account.driver.execute_script("window.stop()")
        # for cookie in _account.driver.get_cookies():
        #     _account.sess.cookies.set(cookie['name'], cookie['value'])
        # _account.hasLoggedIn = True
        # _account.driver.execute_script("console.warn(document.cookie)")
        # _account.driver.delete_all_cookies()

        # logging.warning('loggedIn')
        # cookies maxAge
        # sleep(20 * 60)
