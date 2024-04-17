from instagram_scrapper import instagram_profile_info
from instagram_bd_insert import insert_user_into_my_bd
from instagram_transaction import instagram_transaction


def instagram_scrapping_and_transaction(user_id, tweets_flag=0, followers_flag=0, answers_flag=0, daterange=0):
    # Скрапим информацию о пользователе
    print("Scrapping...")
    user_info = instagram_profile_info(user_id)
    print("DONE!")

    # Вставляем информацию в базу данных
    print("Insert into my bd...")
    insert_user_into_my_bd(user_info)
    print("DONE!")

    # Переносим на ресурс
    print("Transaction...")
    instagram_transaction(user_info, daterange)
    print("DONE!")

    print(user_info)

instagram_scrapping_and_transaction('')