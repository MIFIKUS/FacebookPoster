from FB.Groups.find import find_all_groups
from FB.Groups.research import research_group
from FB.Login.login import make_login
from FB.Groups.post import make_post
from DeepSeek.ds import change_text

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import time

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--window-size=1920,1080")
driver = webdriver.Chrome(options=chrome_options)

make_login(driver, 'mifikus322@gmail.com', 'qwertqwert58702')
groups = find_all_groups(driver, 'Пельмени')
print(groups)

for name, link in groups.items():
    group_info = research_group(driver, link)

    posts_str = ''
    for post_link, post_info in group_info['posts'].items():
        post_text = post_info['text']
        comments = post_info['comments']
        posts_str += f'Текст поста: {post_text}\nКомментарии: {"\n".join(comments)}\n'

    post_text = change_text('пельмени это хорошо', name, posts_str, group_info['desc'])
    print(post_text)
    make_post(driver, post_text, link)
time.sleep(1000)



print(a)