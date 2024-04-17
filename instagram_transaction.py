from pprint import pprint
from selenium import webdriver
from instagram_scrapper import main_info
from instagram_bd_insert import insert_main_info
from insert_functions import insert_row_twitchack
from insert_functions import select_instagram
import hashlib
import datetime
from threading import Thread
from queue import Queue


def generate_used_users(user_info):
    # Идем по твитам и ответам и добавляем аккаунты, которые взаимодейтсвуют с запрашиваемым
    list_used_users = []
    for post in user_info['posts']:
        for answer in post['answers']:
            if answer['user_id'] not in list_used_users:
                list_used_users.append(answer['user_id'])
        for user in post['liker_list']:
            if user not in list_used_users:
                list_used_users.append(user)

    # Добавляем сюда же подписчиков и подписки
    for user in user_info['followers_list']:
        if user not in list_used_users:
            list_used_users.append(user)

    for user in user_info['following_list']:
        if user not in list_used_users:
            list_used_users.append(user)

    return list_used_users


def additional_scrapping_used_users(users_list):
    browser = webdriver.Chrome(executable_path=r"chromedriver.exe")
    info_about_used_users = []
    for user in users_list:
        print(user)
        info_about_used_users.append(main_info(user, browser))

    return info_about_used_users


def create_multithreading(function, data):
    result_list = []

    # Формируем очередь потоков и исполянем функцию с поделенными данными по полам
    queue = Queue()
    threads_list = []
    thread1 = Thread(target=lambda q, arg1: q.put(function(arg1)), args=(queue, data[:len(data)//2]))
    thread1.start()
    threads_list.append(thread1)
    thread2 = Thread(target=lambda q, arg1: q.put(function(arg1)), args=(queue, data[len(data)//2:]))
    thread2.start()
    threads_list.append(thread2)

    # Подключаем потоки
    for thread in threads_list:
        thread.join()

    # Вовзразаем значения
    while not queue.empty():
        result_list += queue.get()

    return result_list


def bd_insert_used_users(used_users):
    # Вставляет инфу о всех нужных пользователях в свою бд
    for user in used_users:
        insert_main_info(user)


def select_user_on_userid(user_id):
    select_query = 'SELECT id from users WHERE username=%s'
    try:
        user_instagram_id = select_instagram(select_query, [user_id, ])[0][0]
    except IndexError:
        user_instagram_id = None
    return user_instagram_id


def instagram_bd_insert_user_info(user_info):
    query = 'INSERT INTO users(id, username, firstname, surname, email, password, facebook, instagram, twitter, youtube, ' \
            'website, mobile, bio, type, signup, email_activated, last_login, pri_ip, pri_os, pri_browser)' \
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ' \
            'ON DUPLICATE KEY UPDATE id=VALUES(id), username=VALUES(username), firstname=VALUES(firstname), ' \
            'surname=VALUES(surname), email=VALUES(email), password=VALUES(password), facebook=VALUES(facebook), ' \
            'instagram=VALUES(instagram), twitter=VALUES(twitter), youtube=VALUES(youtube), website=VALUES(website), ' \
            'mobile=VALUES(mobile), bio=VALUES(bio), type=VALUES(type), signup=VALUES(signup), ' \
            'email_activated=VALUES(email_activated), last_login=VALUES(last_login), pri_ip=VALUES(pri_ip), ' \
            'pri_os=VALUES(pri_os), pri_browser=VALUES(pri_browser)'

    info_list = []
    for user in user_info:
        info_list.append([int(hashlib.sha1((user['user_id']).encode()).hexdigest(), 16) % (10**10),
                          user['user_id'], user["name"], "", user['user_id']+"@yandex.ru",
                          hashlib.sha1(b"123123").hexdigest(), "", "", "",  "",  "",  "", user['description'],
                          user['type'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 'yes',
                          datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "1", "Windows 10", "Chrome"])
    insert_row_twitchack(query, info_list)


def instagram_bd_insert_followers(user_info):
    # Проходим по подписчикам и подписываемся
    query = 'INSERT INTO follow_system(follow_id, follow_by, follow_by_u, follow_to, follow_to_u, time) ' \
                    'VALUES (%s, %s, %s, %s, %s, %s) ' \
                    'ON DUPLICATE KEY UPDATE follow_id=VALUES(follow_id), follow_by=VALUES(follow_by), follow_by_u=VALUES(follow_by_u), ' \
                    'follow_to=VALUES(follow_to), follow_to_u=VALUES(follow_to_u)'

    user_instagram_id = select_user_on_userid(user_info['user_id'])

    # Привязываем подписчиков
    followers = []
    following = []
    follower_info = []
    for user in user_info['followers_list']:
        if select_user_on_userid(user):
            followers.append({
                    'id': select_user_on_userid(user),
                    'user_id': user,
                }
            )
    for follower in followers:
        info = [(follower['id'] + user_instagram_id) % (10**10),
                follower['id'], follower['user_id'], user_instagram_id, user_info['user_id'],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        follower_info.append(info)

    # Привязываем подписки
    for user in user_info['following_list']:
        if select_user_on_userid(user):
            following.append({
                    'id': select_user_on_userid(user),
                    'user_id': user,
                }
            )
    for follower in following:
        info = [(follower['id'] + user_instagram_id) % (10**9),
                user_instagram_id, user_info['user_id'], follower['id'], follower['user_id'],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        follower_info.append(info)

    print('     ' + str(len(follower_info)) + 'Followers and Following insert')
    insert_row_twitchack(query, follower_info)


def instagram_bd_insert_post(user_info, daterange=0):
    query = 'INSERT INTO post(post_id, user_id, type, post_of, grp_id, time, font_size, address) ' \
            'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)' \
            'ON DUPLICATE KEY UPDATE post_id=VALUES(post_id), user_id=VALUES(user_id),type=VALUES(type), post_of=VALUES(post_of),' \
            'grp_id=VALUES(grp_id), time=VALUES(time), font_size=VALUES(font_size), address=VALUES(address)'

    image_query = 'INSERT INTO image_post(image_post_id, post_id, image, about, filter)' \
                  'VALUES (%s, %s, %s, %s, %s)' \
                  'ON DUPLICATE KEY UPDATE image_post_id=VALUES(image_post_id), post_id=VALUES(post_id),' \
                  'image=VALUES(image), about=VALUES(about), filter=VALUES(filter)'

    video_query = 'INSERT INTO video_post(video_post_id, post_id, video, about) ' \
                  'VALUES (%s, %s, %s, %s)' \
                  'ON DUPLICATE KEY UPDATE video_post_id=VALUES(video_post_id), post_id=VALUES(post_id),' \
                  'video=VALUES(video), about=VALUES(about),'

    post_info = []
    user_instagram_id = select_user_on_userid(user_info['user_id'])
    video_post_info = []
    image_post_info = []

    for post in user_info['posts']:
        # Добавляем данные в таблицу post
        info = [int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8), user_instagram_id,
                post['post_type'], "user", 0, post['timestamp_of_post'], 14, ""]
        post_info.append(info)

        # Добавляем данные в таблицу конкретного вида поста
        if post['post_type'] == 'image':
            image_info = [int(hashlib.sha1((post['post_id'] + 'image').encode()).hexdigest(), 16) % (10**6),
                          int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8), post['media_src'],
                          post['text'], ""]
            image_post_info.append(image_info)
        else:
            video_info = [int(hashlib.sha1((post['post_id'] + 'video').encode()).hexdigest(), 16) % (10**6),
                          int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16), post['media_src'],
                          post['text']]
            video_post_info.append(video_info)

    insert_row_twitchack(query, post_info)
    insert_row_twitchack(image_query, image_post_info)
    insert_row_twitchack(video_query, video_post_info)


def instagram_bd_insert_answers(user_info, daterange):
    query = 'INSERT INTO post_comments(post_comments_id, post_id, user_id, data, type, time) ' \
            'VALUES (%s, %s, %s, %s, %s, %s) ' \
            'ON DUPLICATE KEY UPDATE post_comments_id=VALUES(post_comments_id), post_id=VALUES(post_id), ' \
            'user_id=VALUES(user_id), data=VALUES(data), type=VALUES(type), time=VALUES(time)'

    answer_info = []
    for post in user_info['posts']:
        for answer in post['answers']:
            if answer['text'] and select_user_on_userid(answer['user_id']):
                info = [int(hashlib.sha1((post["post_id"] + answer["text"]).encode()).hexdigest(), 16) % (10**6),
                        int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8),
                        select_user_on_userid(answer['user_id']),
                        answer['text'], 'text', answer['timestamp_of_answer']]
                answer_info.append(info)

    insert_row_twitchack(query, answer_info)


def instagram_bd_insert_likes(user_info):
    query = 'INSERT INTO post_likes(post_likes_id, post_like_by, post_id, time) ' \
            'VALUES (%s, %s, %s, %s) ' \
            'ON DUPLICATE KEY UPDATE post_likes_id=VALUES(post_likes_id), post_like_by=VALUES(post_like_by), ' \
            'post_id=VALUES(post_id), time=VALUES(time)'

    likes_info = []
    for post in user_info['posts']:
        for user in post["liker_list"]:
            if select_user_on_userid(user):
            # if date >= datetime.datetime.strptime(daterange[0], "%m.%d.%Y") and date <= datetime.datetime.strptime(daterange[1], "%m.%d.%Y"):
                info = [int(hashlib.sha1((post['post_id'] + user).encode()).hexdigest(), 16) % (10**7),
                        select_user_on_userid(user), int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8),
                        post['timestamp_of_post']]
                likes_info.append(info)

    insert_row_twitchack(query, likes_info)


def instagram_transaction(user_info, daterange=0):
    # Отбор взаимодейтсвующих аккаунтов с переносимым
    used_users = generate_used_users(user_info)
    try:
        used_users.remove(user_info['name'])
    except ValueError:
        pass
    # Дополнительно скрапим используемых пользователей
    print(' Scrapping additional users... 1/7')
    info_about_used_users = create_multithreading(additional_scrapping_used_users, used_users)
    print(' Done... 1/7')

    pprint(info_about_used_users)
    # info_about_used_users = all_users

    # Вставляем информацию о используемых пользователях в своб бд
    print(' Insert users into bd... 2/7')
    bd_insert_used_users(info_about_used_users)
    print(' Done... 2/7')

    # Создаем пользователя и доп пользователей в сети
    print(' Insert users into social... 3/7')
    instagram_bd_insert_user_info([user_info] + info_about_used_users)
    print(' Done... 3/7')

    # Подписываем пользователей на пользователя и его на них
    print(' Insert followers info into social... 4/7')
    instagram_bd_insert_followers(user_info)
    print(' Done... 4/7')

    # Выкладываем посты, в том числе и ретвиты
    #daterange = daterange.split(' - ')
    print(' Insert posts into social... 5/7')
    instagram_bd_insert_post(user_info, daterange)
    print(' Done... 5/7')

    print(' Insert answers into social... 6/7')
    instagram_bd_insert_answers(user_info, daterange)
    print(' Done... 6/7')

    print(' Insert likes into social... 7/7')
    instagram_bd_insert_likes(user_info)
    print(' Done... 7/7')

#instagram_transaction(result)
