from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, JavascriptException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from FB.utils.waits import wait_for_presence
import traceback

from urllib.parse import quote
import time


def find_all_groups(driver: webdriver.Chrome, keyword: str) -> dict:
    #работает таким образом что собирает set групп, и удаляет из dom все дивы групп которые он уже просмотрел
    url_encoded_keyword = quote(keyword)

    driver.get(f'https://www.facebook.com/groups/search/groups_home/?q={url_encoded_keyword}')

    all_found_groups = []

    ready_groups = {}
    result_lines = []

    counter = 0
    while True:
        if counter == 500:
            break
        # Проверяем, есть ли элемент "Результатов больше нет"
        try:
            driver.find_element(By.XPATH, "//span[text()='Результатов больше нет']")
            print("Достигнут конец результатов поиска")
            break
        except NoSuchElementException:
            pass

        try:
            feed_div = wait_for_presence(driver, By.XPATH, '//div[@role="feed"]', 15)
        except TimeoutException:
            break
        groups = feed_div.find_elements(By.XPATH, './/a[@role="presentation"]')

        removed_any = False

        for group in groups:
            try:
                link = group.get_attribute('href')
            except StaleElementReferenceException as e:
                # элемент устарел — просто пропускаем, перезапросим весь список в следующей итерации
                traceback.print_exc()
                print(f"StaleElementReferenceException при получении ссылки: {str(e)}")
                continue

            if not link:
                continue

            if link in all_found_groups:
                # Попытка удалить предка с data-virtualized="false" (гибкая проверка)
                try:
                    removed = driver.execute_script("""
                        let el = arguments[0];
                        while (el && el !== document) {
                            if (el.tagName === 'DIV' && el.hasAttribute('data-virtualized')) {
                                let val = el.getAttribute('data-virtualized');
                                // считаем false, null, undefined, empty или строку "false" как false-показатель
                                if (val === null || String(val).trim().toLowerCase() === 'false' || String(val).trim() === '') {
                                    el.remove();
                                    return true;
                                }
                            }
                            el = el.parentElement;
                        }
                        return false;
                    """, group)
                except (StaleElementReferenceException, JavascriptException) as e:
                    # если элемент стал stale между чтением и вызовом JS — пропустим; перезапросим позже
                    traceback.print_exc()
                    print(f"Ошибка при удалении элемента: {str(e)}")
                    removed = False

                if removed:
                    print(f"Removed ancestor for link: {link}")
                    removed_any = True
                    # После изменения DOM безопаснее прервать текущую обработки и перезапросить элементы
                    break

                # если не удалили — можно пробовать подняться выше и удалить любые matching предки (альтернатива)
                # либо скрыть элемент вместо удаления:
                # driver.execute_script("arguments[0].style.display='none'", group)

                continue

            # если ссылка новая — обрабатываем
            try:
                title = group.text
                counter += 1
            except StaleElementReferenceException as e:
                # если элемент стал устаревшим до чтения текста, пропустим — перезапустим цикл
                traceback.print_exc()
                print(f"StaleElementReferenceException при чтении текста: {str(e)}")
                continue

            ready_groups[title] = link
            all_found_groups.append(link)
            result_lines.append(f"{title}: {link}")

        if removed_any:
            # маленькая пауза, чтобы DOM успел стабилизироваться
            time.sleep(0.1)
            # перезапускаем основной while — это перезапросит feed_div и groups
            continue
        # Возвращаем найденные группы в формате "название: ссылка"
    return ready_groups





