from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from urllib.parse import urlparse

import time

def research_group(driver: webdriver.Chrome, url: str) -> dict:
    wait = WebDriverWait(driver, 15)
    driver.get(url)
    driver.execute_script("window.scrollBy(0, 200);")
    try:
        reveal_description_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@role='button' and text()='Ещё']"))
        )
        reveal_description_button.click()
    except TimeoutException:
        pass

    try:
        all_descriptions = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//div[@dir='auto']"))
        )
    except TimeoutException:
        all_descriptions = []
    description_raw = []

    for i in all_descriptions:
        description_part = i.text
        if description_part.endswith('Меньше'):
            break
        description_raw.append(description_part)

    description = "\n".join(description_raw)

    try:
        all_posts = wait.until(
            EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'https://www.facebook.com/groups/') and contains(@href, 'posts') and not(contains(@href, 'comment_id'))]"))
        )
    except TimeoutException:
        all_posts = []
    # Пролистываем страницу вниз на полный экран два раза
    for _ in range(2):
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(0.5)

    unique_links = {}
    for el in all_posts:
        try:
            href = el.get_attribute("href")
            if href:
                parsed = urlparse(href)
                base = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"  # чистая ссылка без query
                # сохраняем только первую полную ссылку, найденную для base
                if base not in unique_links:
                    unique_links[base] = href 
        except:
            pass

    all_posts_link = list(unique_links.values())

    posts_data = {}
    for post in all_posts_link:
        driver.get(post)

        try:
            post_text_el = wait.until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-ad-comet-preview='message' and @data-ad-preview='message']"))
            )
            post_text = post_text_el.text
        except TimeoutException:
            post_text = ""

        try:
            comments = wait.until(
                EC.presence_of_all_elements_located((By.XPATH, "//span[@dir='auto' and @lang='ru-RU']"))
            )
        except TimeoutException:
            comments = []

        posts_data[post] = {
            "text": post_text,
            "comments": [c.text for c in comments if c.text]
        }

    return {"desc": description, "posts": posts_data}




