import telebot
from telebot import types
import json
import os
import threading
import traceback
import tempfile
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from FB.Groups.find import find_all_groups
from FB.Groups.research import research_group
# from FB.Login.login import make_login
from FB.Groups.post import make_post
from DeepSeek.ds import change_text

# Инициализация бота
bot = telebot.TeleBot("8400282082:AAEFh5oZXxZNgyiw-jE2ZpAzVJ1vZ_UfR1g")  # Замените на ваш токен

# Файлы для хранения данных
CONFIG_FILE = "bot_config.json"
PROMPT_FILE = "DeepSeek/promt.txt"
PREVIEW_FILE = "preview_posts.txt"

# Загрузка конфигурации
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
            # Обратная совместимость: добавляем поле cookies_file, если его нет
            if "cookies_file" not in cfg:
                cfg["cookies_file"] = ""
            # Удаляем устаревшее поле login, если оно есть
            if "login" in cfg:
                cfg.pop("login", None)
            return cfg
    return {
        "cookies_file": "",
        "keywords": [],
        "post_text": "",
        "prompt": ""
    }
def _auth_with_cookies(driver, cookies_file_path):
    driver.get("https://www.facebook.com/")
    # Загружаем cookies
    with open(cookies_file_path, "r", encoding="utf-8") as f:
        cookies = json.load(f)
    # Добавляем cookies
    for cookie in cookies:
        cookie_dict = {
            "name": cookie.get("name"),
            "value": cookie.get("value"),
            "domain": cookie.get("domain", ".facebook.com"),
            "path": cookie.get("path", "/"),
        }
        if "expiry" in cookie:
            cookie_dict["expiry"] = cookie.get("expiry")
        try:
            driver.add_cookie(cookie_dict)
        except Exception:
            # Пропускаем некорректные cookies
            pass
    # Применяем cookies
    driver.get("https://www.facebook.com/")
# Сохранение конфигурации
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

# Загрузка промпта
def load_prompt():
    if os.path.exists(PROMPT_FILE):
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            return f.read()
    return ""

# Сохранение промпта
def save_prompt(prompt_text):
    with open(PROMPT_FILE, "w", encoding="utf-8") as f:
        f.write(prompt_text)

# Сохранение превью постов
def save_preview_posts(posts_data):
    with open(PREVIEW_FILE, "w", encoding="utf-8") as f:
        for group_name, post_text in posts_data.items():
            f.write(f"{group_name}\n{post_text}\n\n")

# Загрузка превью постов
def load_preview_posts():
    if not os.path.exists(PREVIEW_FILE):
        return {}

    posts_data = {}
    with open(PREVIEW_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        if content:
            groups = content.split("\n\n")
            for group in groups:
                if group.strip():
                    lines = group.strip().split("\n", 1)
                    if len(lines) == 2:
                        posts_data[lines[0]] = lines[1]
    return posts_data

# Состояния пользователей
user_states = {}

@bot.message_handler(commands=["start"])
def start_message(message):
    config = load_config()
    markup = types.InlineKeyboardMarkup()

    markup.add(types.InlineKeyboardButton("📝 Задать промпт", callback_data="set_prompt"))
    markup.add(types.InlineKeyboardButton("🍪 Загрузить cookies", callback_data="set_cookies"))
    markup.add(types.InlineKeyboardButton("🔍 Задать ключевые слова", callback_data="set_keywords"))
    markup.add(types.InlineKeyboardButton("📄 Задать пост", callback_data="set_post"))
    markup.add(types.InlineKeyboardButton("🔍 Создать превью постов", callback_data="create_preview"))
    markup.add(types.InlineKeyboardButton("🚀 Запустить рассылку", callback_data="run_script"))

    bot.send_message(
        message.chat.id,
        f"🤖 Добро пожаловать в Facebook Poster Bot!\n\n"
        f"📊 Текущие настройки:\n"
        f"• Cookies: {'✅ Загружены' if config.get('cookies_file') else '❌ Не загружены'}\n"
        f"• Ключевые слова: {len(config['keywords'])} шт.\n"
        f"• Пост: {'✅ Задан' if config['post_text'] else '❌ Не задан'}\n"
        f"• Промпт: {'✅ Настроен' if config['prompt'] else '❌ Не настроен'}\n\n"
        f"💡 Сначала создайте превью постов, затем запустите рассылку",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "set_prompt")
def set_prompt_callback(call):
    bot.answer_callback_query(call.id)
    user_states[call.from_user.id] = "waiting_prompt"

    current_prompt = load_prompt()
    bot.send_message(
        call.message.chat.id,
        f"📝 Введите новый промпт для DeepSeek.\n\n"
        f"Доступные переменные:\n"
        f"• {{text}} - текст поста от пользователя\n"
        f"• {{group_name}} - название группы\n"
        f"• {{group_desc}} - описание группы\n"
        f"• {{posts}} - список постов и комментариев группы\n\n"
        f"Текущий промпт:\n{current_prompt}",
        parse_mode="Markdown"
    )

@bot.callback_query_handler(func=lambda call: call.data == "set_cookies")
def set_cookies_callback(call):
    bot.answer_callback_query(call.id)
    user_states[call.from_user.id] = "waiting_cookies_file"
    bot.send_message(
        call.message.chat.id,
        "🍪 Отправьте файл cookies в формате JSON, экспортированный из вашего браузера.\n\n"
        "Требования:\n"
        "- Файл должен содержать массив объектов cookie с полями name, value, domain, path, expiry (при наличии).\n"
        "- Рекомендуемый домен: .facebook.com\n\n"
        "Просто прикрепите файл сюда сообщением."
    )

@bot.callback_query_handler(func=lambda call: call.data == "set_keywords")
def set_keywords_callback(call):
    bot.answer_callback_query(call.id)
    user_states[call.from_user.id] = "waiting_keywords"
    config = load_config()
    current_keywords = ", ".join(config["keywords"]) if config["keywords"] else "Нет"
    bot.send_message(
        call.message.chat.id,
        f"🔍 Введите ключевые слова через запятую:\n\nТекущие: {current_keywords}"
    )

@bot.callback_query_handler(func=lambda call: call.data == "set_post")
def set_post_callback(call):
    bot.answer_callback_query(call.id)
    user_states[call.from_user.id] = "waiting_post"
    config = load_config()
    current_post = config["post_text"] if config["post_text"] else "Нет"
    bot.send_message(
        call.message.chat.id,
        f"📄 Введите текст поста (будет использован как {{text}} в промпте):\n\nТекущий: {current_post}"
    )

@bot.callback_query_handler(func=lambda call: call.data == "create_preview")
def create_preview_callback(call):
    bot.answer_callback_query(call.id)
    config = load_config()

    # Проверяем, что все настройки заданы
    if not config.get("cookies_file") or not os.path.exists(config["cookies_file"]):
        bot.send_message(call.message.chat.id, "❌ Сначала загрузите файл cookies!")
        return

    if not config["keywords"]:
        bot.send_message(call.message.chat.id, "❌ Сначала задайте ключевые слова!")
        return

    if not config["post_text"]:
        bot.send_message(call.message.chat.id, "❌ Сначала задайте текст поста!")
        return

    if not load_prompt():
        bot.send_message(call.message.chat.id, "❌ Сначала задайте промпт!")
        return

    # Запускаем создание превью в отдельном потоке
    thread = threading.Thread(target=create_posts_preview, args=(call.message.chat.id, config))
    thread.daemon = True
    thread.start()

    bot.send_message(call.message.chat.id, "🔍 Создание превью постов... Ожидайте уведомления...")

@bot.callback_query_handler(func=lambda call: call.data == "run_script")
def run_script_callback(call):
    bot.answer_callback_query(call.id)

    # Проверяем, есть ли превью постов
    preview_posts = load_preview_posts()
    if not preview_posts:
        bot.send_message(call.message.chat.id, "❌ Сначала создайте превью постов!")
        return

    # Показываем кнопки для подтверждения или редактирования
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("✅ Подтвердить и запустить", callback_data="confirm_posts"))
    markup.add(types.InlineKeyboardButton("✏️ Изменить комментарии", callback_data="edit_posts"))

    bot.send_message(
        call.message.chat.id,
        f"📋 Найдено {len(preview_posts)} постов для публикации.\n\n"
        f"Выберите действие:",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == "confirm_posts")
def confirm_posts_callback(call):
    bot.answer_callback_query(call.id)

    # Запускаем рассылку в отдельном потоке
    thread = threading.Thread(target=run_facebook_script, args=(call.message.chat.id,))
    thread.daemon = True
    thread.start()

    bot.send_message(call.message.chat.id, "🚀 Рассылка запущена! Ожидайте уведомления...")

@bot.callback_query_handler(func=lambda call: call.data == "edit_posts")
def edit_posts_callback(call):
    bot.answer_callback_query(call.id)
    user_states[call.from_user.id] = "waiting_edited_posts"

    bot.send_message(
        call.message.chat.id,
        "✏️ Отправьте текстовый файл с отредактированными постами.\n\n"
        "Формат файла:\n"
        "название_группы\n"
        "текст_поста\n\n"
        "название_группы2\n"
        "текст_поста2\n\n"
        "И так далее..."
    )

def create_posts_preview(chat_id, config):
    driver = None
    temp_profile_dir = None
    try:
        # Настройка Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        #chrome_options.add_argument("--no-sandbox")
        #chrome_options.add_argument("--disable-dev-shm-usage")
        # Уникальный профиль для избежания конфликта user-data-dir
        temp_profile_dir = tempfile.mkdtemp(prefix="fbposter_chrome_")
        chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")

        driver = webdriver.Chrome(options=chrome_options)

        # Логин по cookies
        bot.send_message(chat_id, "🔐 Авторизация через cookies...")
        _auth_with_cookies(driver, config["cookies_file"])
        bot.send_message(chat_id, "✅ Cookies применены!")

        # Обработка ключевых слов
        all_groups = {}
        for keyword in config["keywords"]:
            bot.send_message(chat_id, f"🔍 Поиск групп по ключевому слову: {keyword}")
            groups = find_all_groups(driver, keyword)

            # Удаляем дубликаты
            for name, link in groups.items():
                if name not in all_groups:
                    all_groups[name] = link

        bot.send_message(chat_id, f"📊 Найдено {len(all_groups)} уникальных групп")

        # Создание превью постов
        preview_posts = {}
        success_count = 0
        error_count = 0

        for name, link in all_groups.items():
            try:
                bot.send_message(chat_id, f"📋 Исследование группы: {name}")
                group_info = research_group(driver, link)

                # Формируем строку с постами
                posts_str = ""
                for post_link, post_info in group_info["posts"].items():
                    post_text = post_info.get("text", "")
                    comments = post_info.get("comments", [])
                    posts_str += f"Текст поста: {post_text}\nКомментарии: {'; '.join(comments)}\n"

                # Генерируем пост с помощью DeepSeek
                bot.send_message(chat_id, f"🤖 Генерация поста для группы: {name}")
                generated_post = change_text(
                    config["post_text"],
                    name,
                    posts_str,
                    group_info.get("desc", "")
                )

                preview_posts[link] = generated_post
                success_count += 1

                bot.send_message(chat_id, f"✅ Пост сгенерирован для группы: {name}")

            except Exception as e:
                error_count += 1
                bot.send_message(chat_id, f"❌ Ошибка в группе {name}: {str(e)}")

        # Сохраняем превью постов
        save_preview_posts(preview_posts)

        # Отправляем файл с превью
        if preview_posts:
            with open(PREVIEW_FILE, "rb") as f:
                bot.send_document(chat_id, f, caption=f"📄 Превью постов ({len(preview_posts)} шт.)")

        # Итоговый отчет
        bot.send_message(
            chat_id,
            f"📊 Создание превью завершено!\n"
            f"✅ Успешно: {success_count}\n"
            f"❌ Ошибок: {error_count}\n\n"
            f"Теперь можете запустить рассылку или отредактировать посты."
        )

    except Exception as e:
        bot.send_message(chat_id, f"❌ Критическая ошибка при создании превью: {str(e)}")

    finally:
        if driver:
            driver.quit()
        if temp_profile_dir and os.path.isdir(temp_profile_dir):
            shutil.rmtree(temp_profile_dir, ignore_errors=True)

def run_facebook_script(chat_id):
    driver = None
    temp_profile_dir = None
    try:
        # Загружаем превью постов
        preview_posts = load_preview_posts()
        if not preview_posts:
            bot.send_message(chat_id, "❌ Нет постов для публикации!")
            return

        # Настройка Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--window-size=1920,1080")
        #chrome_options.add_argument("--no-sandbox")
        #chrome_options.add_argument("--disable-dev-shm-usage")
        # Уникальный профиль для избежания конфликта user-data-dir
        temp_profile_dir = tempfile.mkdtemp(prefix="fbposter_chrome_")
        chrome_options.add_argument(f"--user-data-dir={temp_profile_dir}")

        driver = webdriver.Chrome(options=chrome_options)

        # Логин по cookies
        bot.send_message(chat_id, "🔐 Авторизация через cookies...")
        config = load_config()
        _auth_with_cookies(driver, config["cookies_file"])
        bot.send_message(chat_id, "✅ Cookies применены!")

        # Получаем группы для публикации
        # Публикация постов
        success_count = 0
        error_count = 0

        for group_link, post_text in preview_posts.items():
            try:
                bot.send_message(chat_id, f"📝 Публикация поста в группе: {group_link}")
                make_post(driver, post_text, group_link)
                success_count += 1
                bot.send_message(chat_id, f"✅ Успешно опубликовано в группе: {group_link}")

            except Exception as e:
                traceback.print_exc()
                error_count += 1
                bot.send_message(chat_id, f"❌ Ошибка в группе {group_link}: {str(e)}")


        # Итоговый отчет
        bot.send_message(
            chat_id,
            f"📊 Рассылка завершена!\n"
            f"✅ Успешно: {success_count}\n"
            f"❌ Ошибок: {error_count}"
        )

    except Exception as e:
        bot.send_message(chat_id, f"❌ Критическая ошибка: {str(e)}")

    finally:
        if driver:
            driver.quit()
        if temp_profile_dir and os.path.isdir(temp_profile_dir):
            shutil.rmtree(temp_profile_dir, ignore_errors=True)

@bot.message_handler(content_types=["document"])
def handle_document(message):
    user_id = message.from_user.id

    if user_id not in user_states:
        return

    try:
        # Скачиваем файл
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)

        state = user_states[user_id]

        if state == "waiting_edited_posts":
            # Сохраняем временный файл
            temp_file = "temp_edited_posts.txt"
            with open(temp_file, "wb") as f:
                f.write(downloaded_file)

            # Читаем и парсим файл
            with open(temp_file, "r", encoding="utf-8") as f:
                content = f.read().strip()

            if not content:
                bot.send_message(message.chat.id, "❌ Файл пустой!")
                return

            # Парсим посты
            posts_data = {}
            groups = content.split("\n\n")
            for group in groups:
                if group.strip():
                    lines = group.strip().split("\n", 1)
                    if len(lines) == 2:
                        posts_data[lines[0]] = lines[1]

            if not posts_data:
                bot.send_message(message.chat.id, "❌ Неверный формат файла!")
                return

            # Сохраняем отредактированные посты
            save_preview_posts(posts_data)

            # Удаляем временный файл
            os.remove(temp_file)

            del user_states[user_id]

            # Показываем кнопки для подтверждения
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("✅ Подтвердить и запустить", callback_data="confirm_posts"))
            markup.add(types.InlineKeyboardButton("✏️ Изменить еще раз", callback_data="edit_posts"))

            bot.send_message(
                message.chat.id,
                f"✅ Отредактированные посты сохранены! ({len(posts_data)} шт.)\n\n"
                f"Выберите действие:",
                reply_markup=markup
            )

        elif state == "waiting_cookies_file":
            # Сохраняем cookies в файл
            cookies_path = "cookies.json"
            with open(cookies_path, "wb") as f:
                f.write(downloaded_file)

            # Валидация формата JSON
            try:
                with open(cookies_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Ожидался массив cookie")
            except Exception as e:
                os.remove(cookies_path)
                bot.send_message(message.chat.id, f"❌ Некорректный файл cookies: {str(e)}")
                return

            # Сохраняем путь в конфиг
            cfg = load_config()
            cfg["cookies_file"] = cookies_path
            save_config(cfg)

            del user_states[user_id]

            bot.send_message(message.chat.id, "✅ Файл cookies сохранен и готов к использованию!")
        else:
            return

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Ошибка при обработке файла: {str(e)}")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.from_user.id

    if user_id not in user_states:
        return

    state = user_states[user_id]
    config = load_config()

    if state == "waiting_prompt":
        save_prompt(message.text)
        config["prompt"] = message.text
        save_config(config)
        del user_states[user_id]
        bot.send_message(message.chat.id, "✅ Промпт сохранен!")

    # Удалены состояния для логина/пароля

    elif state == "waiting_keywords":
        keywords = [k.strip() for k in message.text.split(",") if k.strip()]
        config["keywords"] = keywords
        save_config(config)
        del user_states[user_id]
        bot.send_message(message.chat.id, f"✅ Сохранено {len(keywords)} ключевых слов!")

    elif state == "waiting_post":
        config["post_text"] = message.text
        save_config(config)
        del user_states[user_id]
        bot.send_message(message.chat.id, "✅ Текст поста сохранен!")

if __name__ == "__main__":
    print("🤖 Бот запущен!")
    bot.infinity_polling()

# Вспомогательная функция авторизации через cookies
