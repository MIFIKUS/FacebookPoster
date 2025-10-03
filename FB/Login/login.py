from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from urllib.parse import urlparse, parse_qs, unquote
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC

from twocaptcha import TwoCaptcha

from FB.Groups.find import find_all_groups

import time


API_KEY = 'a73f96ac0c181b3a1079806627e30d50'
driver = None

captcha_solver = TwoCaptcha(API_KEY)


def _get_login_page():
    driver.get('https://www.facebook.com/')

def _insert_login(login: str):
    login_input = driver.find_element(By.NAME, 'email')
    login_input.send_keys(login)

def _insert_password(password: str):
    login_input = driver.find_element(By.NAME, 'pass')
    login_input.send_keys(password)

def _click_login_button():
    login_button = driver.find_element(By.CLASS_NAME, 'selected').click()

def get_captcha_data():
    while True:
        try:
            driver.switch_to.default_content()
            outer_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "arkose-captcha"))
        )       
            driver.switch_to.frame(outer_iframe)
            url = driver.execute_script("return document.location.href;")
            inner_iframe = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[data-e2e='enforcement-frame']"))
        )       
            driver.switch_to.frame(inner_iframe)
            captcha_data = driver.find_element(By.ID, 'verification-token').get_attribute('value').split('|')

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

