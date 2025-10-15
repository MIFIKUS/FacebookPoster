from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from FB.utils.waits import accept_alert_if_present
from selenium.webdriver.common.action_chains import ActionChains
import traceback

import time

def make_post(driver: webdriver.Chrome, post: str, link: str):
    if post[0] == '-':
        return 'SKIP'
    # Переходим на страницу группы
    post = [1:]
    driver.get(link)
    
    # Ждем загрузки страницы
    wait = WebDriverWait(driver, 60)
    
    try:
        accept_alert_if_present(driver)

        # Ждем появления и кликаем на кнопку создания поста
        make_post_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div[role='button'].x1i10hfl.x1ejq31n.x18oe1m7.x1sy0etr.xstzfhl.x972fbf.x10w94by.x1qhh985.x14e42zd.x9f619.x1ypdohk.x3ct3a4.xdj266r.x14z9mp.xat24cr.x1lziwak.x16tdsg8.x1hl2dhg.xggy1nq.x87ps6o.x1lku1pv.x1a2a7pz.x6s0dn4.xmjcpbm.x12ol6y4.x180vkcf.x1khw62d.x709u02.x78zum5.x1q0g3np.x1iyjqo2.x1nhvcw1.x1n2onr6.xt7dq6l.x1ba4aug.x1y1aw1k.xpdmqnj.xwib8y2.x1g0dm76"))
        )
        make_post_button.click()

        accept_alert_if_present(driver)
        # Ждем появления области для ввода текста
        post_area = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[contenteditable='true'][role='textbox']"))
        )
        accept_alert_if_present(driver)
        result = True
        time.sleep(5)
        for _ in range(300):
        # Вводим текст поста
            try:
                driver.execute_script(f"const el = document.querySelector(\"[contenteditable='true'][aria-placeholder='Создайте общедоступную публикацию…']\"); el.focus(); document.execCommand('insertText', false, '{post}');")
                result = True
                break
            except Exception as e:
                pass
                time.sleep(0.1)
        if result is False:
            raise ValueError
        # Небольшая пауза для стабильности
        accept_alert_if_present(driver)
        send_post_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@aria-label='Отправить' and @role='button' and @tabindex='0']")
            )
        )
        accept_alert_if_present(driver)
        send_post_button.click()


        time.sleep(2)
    
    except TimeoutException as e:
        traceback.print_exc()
        print(f"Ошибка: Не удалось найти элементы на странице в течение ожидаемого времени: {str(e)}")
        raise 

    