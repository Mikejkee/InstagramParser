from insert_functions import insert_row
import hashlib


def insert_main_info(user_info):
    query = 'INSERT INTO user_info(user_id, name, description, src_photo) ' \
            'VALUES (%s, %s, %s, %s) ' \
            'ON DUPLICATE KEY UPDATE user_id=VALUES(user_id), name=VALUES(name), description=VALUES(description), ' \
            'src_photo=VALUES(src_photo)'

    info = [user_info['user_id'], user_info["name"], user_info["description"], user_info["src_photo"]]
    insert_row(query, [info, ])


def insert_follow_info(follow_list, user_id, param):
    query = 'INSERT INTO followers(follower_id, user_id) ' \
            'VALUES (%s, %s) ' \
            'ON DUPLICATE KEY UPDATE follower_id=VALUES(follower_id), user_id=VALUES(user_id)'

    follower_info = []
    # Если 0 - то значит подписчики, 1 - читающие
    if param == 0:
        for follower in follow_list:
            info = [follower, user_id]
            follower_info.append(info)
    elif param == 1:
        for follower in follow_list:
            info = [user_id, follower]
            follower_info.append(info)

    insert_row(query, follower_info)


def insert_posts(posts, user_id):
    query = 'INSERT INTO posts(post_id, user_id, count_of_likes, media_src, text, timestamp_of_post) ' \
            'VALUES (%s, %s, %s, %s, %s, %s)' \
            'ON DUPLICATE KEY UPDATE post_id=VALUES(post_id), user_id=VALUES(user_id), ' \
            'count_of_likes=VALUES(count_of_likes), media_src=VALUES(media_src), text=VALUES(text), ' \
            'timestamp_of_post=VALUES(timestamp_of_post)'

    posts_info = []
    for post in posts:
        info = [int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8), user_id,
                post["count_of_likes"], post['media_src'], post["text"], post["timestamp_of_post"]]
        posts_info.append(info)

    insert_row(query, posts_info)


def insert_answers(posts, user_info):
    query = 'INSERT INTO answers(answer_id, post_id, user_id, text, timestamp_of_answer) ' \
            'VALUES (%s, %s, %s, %s, %s) ' \
            'ON DUPLICATE KEY UPDATE answer_id=VALUES(answer_id), post_id=VALUES(post_id), user_id=VALUES(user_id), ' \
            'text=VALUES(text), timestamp_of_answer=VALUES(timestamp_of_answer)'

    answers_info = []
    for post in posts:
        for answer in post["answers"]:
            info = [int(hashlib.sha1((post["post_id"] + answer["text"]).encode()).hexdigest(), 16) % (10**6),
                    int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8), user_info,
                    answer["text"], answer["timestamp_of_answer"]]
            answers_info.append(info)

    insert_row(query, answers_info)


def insert_likes(posts, user_info):
    query = 'INSERT INTO post_likes(like_id, post_id, user_id) ' \
            'VALUES (%s, %s, %s) ' \
            'ON DUPLICATE KEY UPDATE like_id=VALUES(like_id), post_id=VALUES(post_id), user_id=VALUES(user_id)'

    likes_info = []
    for post in posts:
        for user in post["liker_list"]:
            info = [int(hashlib.sha1((post['post_id'] + user).encode()).hexdigest(), 16) % (10**7),
                    int(hashlib.sha1((post['post_id']).encode()).hexdigest(), 16) % (10**8), user]
            likes_info.append(info)

    insert_row(query, likes_info)


def insert_user_into_my_bd(user_info):
    # Вставляем основную информацию
    print(' Insert main... 1/6')
    insert_main_info(user_info)
    print(' Done... 1/6')
    print('Insert followers and following... 2/6')
    insert_follow_info(user_info['followers_list'], user_info['user_id'], 0)
    insert_follow_info(user_info['following_list'], user_info['user_id'], 1)
    print(' Done... 2/6')

    # Вставляем информацию о постах
    print(' Insert info about posts... 3/6')
    insert_posts(user_info['posts'], user_info['user_id'])
    print(' Done... 3/6')

    # Вставляем информацию об ответах к постам
    print(' Insert info about answers... 4/6')
    insert_answers(user_info['posts'], user_info['user_id'])
    print(' Done... 5/6')

    # Вставляем информацию о лайках к постам
    print(' Insert info about likes... 6/6')
    insert_likes(user_info['posts'], user_info['user_id'])
    print(' Done... 6/6')


# insert_user_into_my_bd(result)
