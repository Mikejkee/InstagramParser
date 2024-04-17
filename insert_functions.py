import mysql.connector
from mysql.connector import Error


# Connect to BD
# —-------------------------------------------—
config = {
'user': 'root',
'password': '',
'host': 'localhost',
'database': 'my_instagram',
'raise_on_warnings': True
}

conn = mysql.connector.connect(**config)

# —--------------------------------------------—
# Connect to BD "twitchack"
# —--------------------------------------------—
config_instagram_clone = {
'user': 'root',
'password': 'root',
'host': 'localhost',
'database': 'instagram',
'raise_on_warnings': True
}

conn_instagram_clone = mysql.connector.connect(**config_instagram_clone)

# For insert new row , we use this function to insert posts and comments
def insert_row(query, data):
    try:
        cursor = conn.cursor()
        cursor.executemany(query, data)

        conn.commit()
    except Error as e:
        print('Error:', e)

    finally:
        conn.commit()
        cursor.close()


# Connectin for database instagram_clone
def insert_row_twitchack(query, data):
    try:
        cursor = conn_instagram_clone.cursor()
        cursor.executemany(query, data)

        conn_instagram_clone.commit()
    except Error as e:
        print('Error:', e)

    finally:
        conn_instagram_clone.commit()
        cursor.close()


def select_instagram(query, data):
    try:
        cursor = conn_instagram_clone.cursor()
        cursor.execute(query, data)

        return cursor.fetchall()
    except Error as e:
        print('Error:', e)

    finally:
        cursor.close()