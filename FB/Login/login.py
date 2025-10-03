from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs, unquote
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from FB.utils.waits import wait_and_type, wait_and_click, wait_for_presence

from twocaptcha import TwoCaptcha

from FB.Groups.find import find_all_groups

import time


API_KEY = 'a73f96ac0c181b3a1079806627e30d50'
driver = None

captcha_solver = TwoCaptcha(API_KEY)


def _get_login_page():
    driver.get('https://www.facebook.com/')

def _insert_login(login: str):
    wait_and_type(driver, By.NAME, 'email', login)

def _insert_password(password: str):
    wait_and_type(driver, By.NAME, 'pass', password)

def _click_login_button():
    wait_and_click(driver, By.CLASS_NAME, 'selected')

def get_captcha_data():
    while True:
        try:
            driver.switch_to.default_content()
            outer_iframe = wait_for_presence(driver, By.ID, "arkose-captcha", 10)
            driver.switch_to.frame(outer_iframe)
            url = driver.execute_script("return document.location.href;")
            inner_iframe = wait_for_presence(driver, By.CSS_SELECTOR, "iframe[data-e2e='enforcement-frame']", 10)
            driver.switch_to.frame(inner_iframe)
            captcha_el = wait_for_presence(driver, By.ID, 'verification-token', 10)
            captcha_data = captcha_el.get_attribute('value').split('|')

            site_key = captcha_data[7].split('=')[1]
            surl = captcha_data[11].split('=')[1]
            return {'site-key': site_key, 'url': url, 'surl': surl}
        except Exception as e:
            print(e)
            pass


def make_login(web_driver: webdriver.Chrome, login: str, password: str):
    global driver
    driver = web_driver
    _get_login_page()

    _insert_login(login)
    _insert_password(password)
    _click_login_button()
    #captcha_data = get_captcha_data()
    
    #resolve = captcha_solver.funcaptcha(sitekey=captcha_data['site-key'], url=captcha_data['url'], surl=captcha_data['surl'])
    #print(resolve)

    input('Нажмите любую кнопку когда капча решена')

