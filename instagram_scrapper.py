from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from datetime import datetime
from bs4 import BeautifulSoup
import time
import re
import wget
import os
import hashlib
import urllib.error
from pprint import pprint

import locale
locale.setlocale(locale.LC_ALL, 'ru')


def list_likers(browser):
    liker_list = []
    # Кликаем
    try:
        browser.find_element_by_css_selector('._0mzm-.sqdOP.yWX7d._8A5w5').click()
        time.sleep(2)

        # Находим всплывающее окно с лайкерами
        #dialog = browser.find_element_by_class_name("isgrP")
        dialog = browser.find_element_by_css_selector(".Igw0E.IwRSH.eGOV_.vwCYk.i0EQd").find_element_by_tag_name('div')
        # Прокручивем его до конца (js)
        last_height = browser.execute_script("return arguments[0].scrollTop", dialog)
        while True:
            browser.execute_script('arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;', dialog)
            time.sleep(2)
            new_height = browser.execute_script("return arguments[0].scrollTop", dialog)
            if new_height == last_height:
                break
            last_height = new_height
        html = BeautifulSoup(browser.page_source, "html.parser")

        for user in html.find_all('div', class_="_7UhW9 xLCgt MMzan KV-D4 fDxYl"):
            liker_list.append(user.contents[0].attrs['title'])

        # Закрываем
        browser.find_element_by_css_selector(".glyphsSpriteX__outline__24__grey_9.u-__7").click()
    except:
        pass
    return liker_list


def list_answers(browser):
    answers_list = []

    try:
        while True:
            button_more = browser.find_element_by_css_selector(".glyphsSpriteCircle_add__outline__24__grey_9.u-__7")
            action = webdriver.ActionChains(browser)
            action.move_to_element(button_more)
            action.perform()
            time.sleep(1)
            button_more.click()
            time.sleep(1)
    except:
        html = BeautifulSoup(browser.page_source, "html.parser")
        for comment in html.find_all('div', class_="C4VMK")[1:]:
            timestamp_of_answer = datetime.strptime(comment.contents[2].contents[0].contents[0].attrs['datetime'][:-14], '%Y-%m-%d').strftime("%Y-%m-%d %H:%M:%S")
            answers_list.append({
                'user_id': comment.contents[0].text,
                'text': comment.contents[1].text,
                'timestamp_of_answer': timestamp_of_answer,
            })

    return answers_list


def info_about_post(browser):
    html = BeautifulSoup(browser.page_source, "html.parser")

    # ID поста
    post_id = re.search(".*/(.*?)/", browser.current_url)[1]

    # Текст поста
    try:
        text = html.find('li', class_="gElp9 rUo9f PpGvg").text
    except AttributeError:
        text = ""

    # Количество лайков
    try:
        count_of_likes = html.find('button', class_="_0mzm- sqdOP yWX7d _8A5w5").contents[0].text
    except AttributeError:
        count_of_likes = 0

    # Дата публикации
    try:
        timestamp_of_post = datetime.strptime(html.find('time', class_="_1o9PC Nzb55").attrs['datetime'][:-14], '%Y-%m-%d').strftime("%Y-%m-%d %H:%M:%S")
    except AttributeError:
        timestamp_of_post = ""

    # Список лайкнувших
    liker_list = list_likers(browser)

    # Ответы
    answers = list_answers(browser)

    post_info = {
        'post_id': post_id,
        'text': text,
        'count_of_likes': count_of_likes,
        'liker_list': liker_list,
        'answers': answers,
        'timestamp_of_post': timestamp_of_post,
    }

    return post_info

def download_media(browser, user):
    # Выкачиваем фотки
    # Пролистываем страницу до конца (загружается js)
    last_height = browser.execute_script("return document.body.scrollHeight")

    posts_info = []
    src_media = []
    while True:
        # Ищем див медии
        for div_img in browser.find_elements_by_class_name("eLAPa"):
            # Проверяем был ли раньше он в списке всех (сделано так, потому что js не прогружает полностью страницу,
            # а страница постоянно генерируется и фиксированное количество медии на ней
            if div_img.find_element_by_class_name("FFVAD").get_attribute("src") not in src_media:
                src_media.append(div_img.find_element_by_class_name("FFVAD").get_attribute("src"))

                # Тыкаем на медиа
                time.sleep(0.5)
                div_img.find_element_by_class_name("_9AhH0").click()
                media_html = BeautifulSoup(browser.page_source, "html.parser")

                # Если видос, то найдется
                try:
                    url_media_file = media_html.find('video', class_="tWeCl").attrs["src"]
                    post_type = 'video'
                except AttributeError:
                    # Иначе это фото
                    url_media_file = div_img.find_element_by_class_name("FFVAD").get_attribute("src")
                    post_type = 'image'

                # Добавляем в список информацию о посте
                time.sleep(1)
                post_info = info_about_post(browser)

                # Скачиваем по реальным урлам медиа
                format = re.search(".*(\..*)\?", url_media_file)
                path_src_photo = '../../dev/Instagram-clone-master/media/Instagram_' + post_info['post_id'] + format[1]
                if not os.path.exists(path_src_photo):
                    filename = wget.download(url_media_file)
                    os.rename(filename, path_src_photo)

                # Добавляем название медии и тип поста
                post_info['media_src'] = post_info['post_id'] + format[1]
                post_info['post_type'] = post_type
                posts_info.append(post_info)

                print('     ' + str(len(posts_info)) + ' post parsed.')

                browser.find_element_by_class_name("ckWGn").click()

        # Листаем вниз
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        # Проверяем на конец страницы
        new_height = browser.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    return posts_info


def list_followers(browser, param):
    # Выкачиваем подпичиков и подписки
    info_bar = browser.find_elements_by_class_name("g47SY")
    info_bar[param].click()
    time.sleep(2)

    # Находим всплывающее окно с подписчиками
    dialog = browser.find_element_by_class_name("isgrP")
    # Прокручивем его до конца (js)
    last_height = browser.execute_script("return arguments[0].scrollTop", dialog)
    while True:
        browser.execute_script('arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;', dialog)
        time.sleep(2)
        new_height = browser.execute_script("return arguments[0].scrollTop", dialog)
        if new_height == last_height:
            break
        last_height = new_height
    html = BeautifulSoup(browser.page_source, "html.parser")
    users_list = []
    for user in html.find_all('a', class_="FPmhX notranslate _0imsa"):
        users_list.append(user.text)

    # Закрываем
    browser.find_element_by_css_selector(".glyphsSpriteX__outline__24__grey_9.u-__7").click()
    return users_list


def main_info(user, browser):
    # Переходим на нужного пользователя
    time.sleep(1)
    browser.get("https://www.instagram.com/" + user)
    time.sleep(1.5)
    html_profile = BeautifulSoup(browser.page_source, "html.parser")

    # Имя профиля и описание
    name = ""
    description = ""
    for tag in html_profile.find('div', class_="-vDIg").contents:
        if tag.name == "h1":
            name = tag.text
        elif tag.name == "span":
            description = tag.text

    # Выкачиваем фото профиля, если закрытый то другой класс
    try:
        src_photo = html_profile.find('span', class_="_2dbep").contents[0].attrs["src"]
        type = "public"
    except AttributeError:
        src_photo = html_profile.find('img', class_="be6sR").attrs["src"]
        type = "private"
    format = re.search(".*(\..*)\?", src_photo)
    src_photo = user + format[1]
    path_src_photo = "../../dev/Instagram-clone-master//users/" + str(int(hashlib.sha1(user.encode()).hexdigest(), 16) % (10**10)) + "/avatar/"

    # path = 'media/' + user + '/'
    if not os.path.exists(path_src_photo):
        os.makedirs(path_src_photo)

    if not os.path.exists(path_src_photo + src_photo):
        try:
            filename = wget.download(html_profile.find('span', class_="_2dbep").contents[0].attrs["src"])
            os.rename(filename, path_src_photo + src_photo)
        except AttributeError:
            # Если закрытый профиль
            filename = wget.download(html_profile.find('img', class_="be6sR").attrs["src"])
            os.rename(filename, path_src_photo + src_photo)
        except urllib.error.HTTPError:
            pass

    main_info = {
        "user_id": user,
        "name": name,
        "description": description,
        "src_photo": src_photo,
        'type': type,
        'scrap_type': 'short'
    }

    return main_info

def instagram_profile_info(user):
    login = ""
    password = ""

    browser = webdriver.Chrome(executable_path=r"chromedriver.exe")
    # Авторизовываемся в инстаграмме для сбора информации нужного профиля (иначе некоторая информация недоступна)
    browser.get("https://www.instagram.com/accounts/login/")
    time.sleep(1)
    input_forms = browser.find_elements_by_css_selector("._2hvTZ.pexuQ.zyHYP")
    input_forms[0].send_keys(login)
    input_forms[1].send_keys(password)
    input_forms[1].submit()
    time.sleep(3)

    # Парсим основную информацию о пользователе
    print(' Parsing main info... 1/4')
    page_info = main_info(user, browser)
    print(' Done... 1/4')

    # Выкачиваем подпичиков и подписки
    print(' Parsing followers... 2/4')
    followers_list = list_followers(browser, 1)
    print(' Done... 2/4')

    print(' Parsing following... 3/4')
    following_list = list_followers(browser, 2)
    print(' Done... 3/4')

    # Выкачиваем всю медиа профиля
    print(' Parsing posts... 4/4')
    posts = download_media(browser, user)
    print(' Done...  4/4')

    browser.close()
    insagram_user_info = {
        'user_id': user,
        'name': page_info['name'],
        'description': page_info['description'],
        'type': page_info['type'],
        "src_photo": page_info['src_photo'],
        'following_list': following_list,
        'followers_list': followers_list,
        'posts': posts,
        'scrap_type': 'full',
        'timestamp_of_scraping': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    pprint(insagram_user_info)
    return insagram_user_info
