import hashlib
import os
from typing import Literal

import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    connection = psycopg2.connect(
        host=os.getenv('POSTGRES_HOST'),
        port=os.getenv('POSTGRES_PORT'),
        dbname=os.getenv('POSTGRES_DB'),
        user=os.getenv('POSTGRES_USER'),
        password=os.getenv('POSTGRES_PASSWORD'),
    )

    return connection


def get_all_games(
        order_by: Literal['id_game', 'rating', 'release_date'] = 'id_game',
        order_direction: Literal['asc', 'desc'] = 'asc',
        **kwargs: dict[Literal[
            'min_release_date', 'max_release_date', 'min_rating',
            'max_rating', 'id_developer', 'id_publisher', 'search_text'
        ], str]
):
    connection = get_connection()
    query = '''SELECT game.id_game, game.game_name, game.description, 
    game.release_date, game.rating, developer.studio_name, 
    publisher.publisher_name 
    FROM game 
    LEFT JOIN developer 
    ON game.id_developer = developer.id_developer 
    LEFT JOIN publisher 
    ON game.id_publisher = publisher.id_publisher
    '''

    query_filter_args = []
    if len(kwargs) > 0:
        filter_mapping = {
            'min_release_date': 'game.release_date >= %s',
            'max_release_date': 'game.release_date <= %s',
            'min_rating': 'game.rating >= %s',
            'max_rating': 'game.rating <= %s',
            'id_developer': 'developer.id_developer =%s',
            'id_publisher': 'publisher.id_publisher =%s',
            'search_text': "game.game_name LIKE %s "
        }

        query_filter_list = []

        for key, value in kwargs.items():
            query_filter_list.append(filter_mapping[key])
            if key == 'search_text':
                query_filter_args.append(f'%{value}%')
            else:
                query_filter_args.append(value)

        query += '\nWHERE ' + '\nAND '.join(query_filter_list)

    order_by_mapping = {'id_game': 'game.id_game',
                        'rating': 'game.rating',
                        'release_date': 'game.release_date'}

    query += f'\nORDER BY {order_by_mapping[order_by]} {order_direction.upper()}'

    try:
        with connection.cursor() as cursor:
            if query_filter_args:
                print(query)
                cursor.execute(query, query_filter_args)
            else:
                cursor.execute(query)
            games = cursor.fetchall()

        if len(games) == 0:
            return None

        column_names = ['id_game', 'game_name', 'description', 'release_date',
                        'rating', 'developer', 'publisher']
        games_dict = []

        for game in games:
            temp_dict = {}
            for key, value in zip(column_names, game):
                temp_dict[key] = value
            games_dict.append(temp_dict)

        return games_dict
    finally:
        connection.close()


def get_game(game_id):
    connection = get_connection()
    query = '''SELECT game.id_game, game.game_name, game.description, 
    game.release_date, game.rating, 
    developer.studio_name, 
    publisher.publisher_name
    FROM game 
    LEFT JOIN developer 
    ON game.id_developer = developer.id_developer 
    LEFT JOIN publisher 
    ON game.id_publisher = publisher.id_publisher
    WHERE game.id_game = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (game_id,))
            game = cursor.fetchone()

        column_names = ['id_game', 'game_name', 'description', 'release_date',
                        'rating', 'developer', 'publisher']
        game_dict = dict(zip(column_names, game))

        return game_dict
    finally:
        connection.close()


def add_game(
        game_name,
        description,
        release_date,
        id_developer,
        rating=0,
        id_publisher=None
):
    connection = get_connection()
    query = '''INSERT INTO game (game_name, description, release_date, 
    rating, id_developer, id_publisher)
    VALUES (%s, %s, %s, %s, %s, %s)'''

    id_developer = int(id_developer)
    if id_publisher is not None:
        id_publisher = int(id_publisher)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                query,
                (game_name, description, release_date,
                 rating, id_developer, id_publisher)
            )
        connection.commit()
    finally:
        connection.close()


def update_game(
        id_game,
        game_name,
        description,
        release_date,
        id_publisher,
        id_developer
):
    connection = get_connection()
    query = '''UPDATE game SET game_name = %s, description = %s, 
    release_date = %s, id_developer = %s, id_publisher = %s 
    WHERE id_game = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (game_name, description, release_date,
                                   id_developer, id_publisher, id_game))
        connection.commit()
    finally:
        connection.close()


def delete_game(id_game):
    connection = get_connection()
    query = "DELETE FROM game WHERE id_game = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game,))
        connection.commit()
    finally:
        connection.close()


def get_all_users():
    connection = get_connection()
    query = '''SELECT id_user, username, password, email 
    FROM users 
    ORDER BY id_user'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            users = cursor.fetchall()

        column_names = ['id_user', 'username', 'password', 'email']
        users_dict = []

        for user in users:
            temp_dict = {}
            for key, value in zip(column_names, user):
                temp_dict[key] = value
            users_dict.append(temp_dict)

        return users_dict
    finally:
        connection.close()


def get_user(id_user):
    connection = get_connection()
    query = '''SELECT id_user, username, password, email FROM users 
    WHERE id_user = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_user,))
            user = cursor.fetchone()

        column_names = ['id_user', 'username', 'password', 'email']
        user_dict = dict(zip(column_names, user))
        return user_dict
    finally:
        connection.close()


def validate_user(username, password):
    connection = get_connection()
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().upper()
    query = '''SELECT id_user, username, password, email
    FROM users 
    WHERE username = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (username,))
            user = cursor.fetchone()

        if user is None or password_hash != user[2]:
            return None

        column_names = ['id_user', 'username', 'password', 'email']
        user_dict = dict(zip(column_names, user))

        return user_dict
    finally:
        connection.close()


def add_user(username, password, email):
    connection = get_connection()
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().upper()
    query = "INSERT INTO users (username, password, email) VALUES (%s, %s, %s)"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query,
                           (username, password_hash, email)
                           )
        connection.commit()
    finally:
        connection.close()


def update_user(id_user, username=None, password=None, email=None):
    connection = get_connection()

    to_update_list = []
    to_update_args = []

    query = "UPDATE users SET "

    if username is not None:
        to_update_list.append('username=%s')
        to_update_args.append(username)
    if password is not None:
        to_update_list.append('password=%s')
        password_hash = (hashlib.sha256(password.encode('utf-8'))
                         .hexdigest().upper())
        to_update_args.append(password_hash)
    if email is not None:
        to_update_list.append('email=%s')
        to_update_args.append(email)

    if not to_update_list:
        connection.close()
        return

    query += ', '.join(to_update_list)
    query += ' WHERE id_user = %s'
    to_update_args.append(id_user)

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, tuple(to_update_args))
        connection.commit()
    finally:
        connection.close()


def delete_user(id_user):
    connection = get_connection()
    query = "DELETE FROM users WHERE id_user = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_user,))
        connection.commit()
    finally:
        connection.close()


def get_all_developers():
    connection = get_connection()
    query = "SELECT id_developer, studio_name, country FROM developer ORDER BY id_developer"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            developers = cursor.fetchall()

        column_names = ['id_developer', 'studio_name', 'country']
        developers_dict = []

        for developer in developers:
            temp_dict = {}
            for key, value in zip(column_names, developer):
                temp_dict[key] = value
            developers_dict.append(temp_dict)

        return developers_dict
    finally:
        connection.close()


def get_developer(id_developer):
    connection = get_connection()
    query = '''SELECT id_developer, studio_name, country
    FROM developer
    WHERE id_developer = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_developer,))
            developer = cursor.fetchone()

        column_names = ['id_developer', 'studio_name', 'country']
        developer_dict = dict(zip(column_names, developer))

        return developer_dict
    finally:
        connection.close()


def add_developer(studio_name, country=None):
    connection = get_connection()
    query = '''INSERT INTO developer (studio_name, country) VALUES (%s, %s)'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (studio_name, country))
        connection.commit()
    finally:
        connection.close()


def update_developer(id_developer, studio_name, country=None):
    connection = get_connection()
    query = '''UPDATE developer SET studio_name = %s, country = %s 
    WHERE id_developer = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (studio_name, country, id_developer))
        connection.commit()
    finally:
        connection.close()


def delete_developer(id_developer):
    connection = get_connection()
    query = "DELETE FROM developer WHERE id_developer = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_developer,))
        connection.commit()
    finally:
        connection.close()


def get_all_publishers():
    connection = get_connection()
    query = '''SELECT id_publisher, publisher_name, country
    FROM publisher'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            publishers = cursor.fetchall()

        column_names = ['id_publisher', 'publisher_name', 'country']
        publishers_dict = []

        for publisher in publishers:
            temp_dict = {}
            for key, value in zip(column_names, publisher):
                temp_dict[key] = value
            publishers_dict.append(temp_dict)

        return publishers_dict
    finally:
        connection.close()


def get_publisher(id_publisher):
    connection = get_connection()
    query = '''SELECT id_publisher, publisher_name, country
    FROM publisher
    WHERE id_publisher = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_publisher,))
            publisher = cursor.fetchone()
        column_names = ['id_publisher', 'publisher_name', 'country']
        publisher_dict = dict(zip(column_names, publisher))

        return publisher_dict
    finally:
        connection.close()


def add_publisher(publisher_name, country=None):
    connection = get_connection()
    query = "INSERT INTO publisher (publisher_name, country) VALUES (%s, %s)"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (publisher_name, country))
        connection.commit()
    finally:
        connection.close()


def update_publisher(id_publisher, publisher_name, country=None):
    connection = get_connection()
    query = '''UPDATE publisher SET publisher_name = %s, country = %s
    WHERE id_publisher = %s'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (publisher_name, country, id_publisher))
        connection.commit()
    finally:
        connection.close()


def delete_publisher(id_publisher):
    connection = get_connection()
    query = "DELETE FROM publisher WHERE id_publisher = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_publisher,))
        connection.commit()
    finally:
        connection.close()


def get_comments(id_game=None, id_user=None):
    connection = get_connection()
    query = '''SELECT comment.id_game, comment.id_user, comment.text, 
    game.game_name, users.username
    FROM comment
    JOIN game ON comment.id_game = game.id_game
    JOIN users ON comment.id_user = users.id_user'''

    filter_list = []
    filter_args = []

    if id_game is not None:
        filter_list.append('comment.id_game=%s')
        filter_args.append(id_game)

    if id_user is not None:
        filter_list.append('comment.id_user=%s')
        filter_args.append(id_user)

    if filter_list:
        query += ' WHERE ' + ' AND '.join(filter_list)

    try:
        with connection.cursor() as cursor:
            if filter_list:
                cursor.execute(query, tuple(filter_args))
            else:
                cursor.execute(query)
            comments = cursor.fetchall()

        column_names = ['id_game', 'id_user', 'text', 'game_name', 'username']
        comments_dict = []

        for comment in comments:
            temp_dict = {}
            for key, value in zip(column_names, comment):
                temp_dict[key] = value
            comments_dict.append(temp_dict)

        return comments_dict
    finally:
        connection.close()


def add_comment(id_game, id_user, comment):
    connection = get_connection()
    query = "INSERT INTO comment (id_game, id_user, text) VALUES (%s, %s, %s)"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game, id_user, comment))
        connection.commit()
    finally:
        connection.close()


def update_comment(id_game, id_user, text):
    connection = get_connection()
    query = "UPDATE comment SET text = %s WHERE id_game = %s AND id_user = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (text, id_game, id_user))
        connection.commit()
    finally:
        connection.close()


def delete_comment(id_game, id_user):
    connection = get_connection()
    query = "DELETE FROM comment WHERE id_game = %s AND id_user = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game, id_user))
        connection.commit()
    finally:
        connection.close()


def get_all_genres():
    connection = get_connection()
    query = "SELECT id_genre, genre_name FROM genre"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query)
            genres = cursor.fetchall()

        column_names = ['id_genre', 'genre_name']
        genres_dict = []

        for genre in genres:
            temp_dict = {}
            for key, value in zip(column_names, genre):
                temp_dict[key] = value
            genres_dict.append(temp_dict)

        return genres_dict
    finally:
        connection.close()


def get_genre(id_genre):
    connection = get_connection()
    query = "SELECT id_genre, genre_name FROM genre WHERE id_genre = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_genre,))
            genre = cursor.fetchone()

        column_names = ['id_genre', 'genre_name']
        genre_dict = dict(zip(column_names, genre))

        return genre_dict
    finally:
        connection.close()


def add_genre(genre_name):
    connection = get_connection()
    query = "INSERT INTO genre (genre_name) VALUES (%s)"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (genre_name,))
        connection.commit()
    finally:
        connection.close()


def update_genre(id_genre, genre_name):
    connection = get_connection()
    query = "UPDATE genre SET genre_name = %s WHERE id_genre = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (genre_name, id_genre))
        connection.commit()
    finally:
        connection.close()


def delete_genre(id_genre):
    connection = get_connection()
    query = "DELETE FROM genre WHERE id_genre = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_genre,))
        connection.commit()
    finally:
        connection.close()


def validate_admin(login, password):
    connection = get_connection()
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest().upper()
    query = "SELECT id, login, password FROM admin WHERE login = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (login, ))
            admin = cursor.fetchone()

        if admin is None or password_hash != admin[2]:
            return None

        column_names = ['id', 'login', 'password']
        admin_dict = dict(zip(column_names, admin))
        return admin_dict
    finally:
        connection.close()


def add_admin(login, password):
    connection = get_connection()
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    query = "INSERT INTO admin (login, password) VALUES (%s, %s)"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (login, password_hash))
        connection.commit()
    finally:
        connection.close()


def get_genre_of_game(id_game=None, id_genre=None):
    connection = get_connection()
    query = '''SELECT genre_of_game.id_game, genre_of_game.id_genre,
    game.game_name, genre.genre_name
    FROM genre_of_game
    JOIN genre ON genre_of_game.id_genre = genre.id_genre
    JOIN game ON genre_of_game.id_game = game.id_game'''

    filter_list = []
    filter_args = []

    if id_game is not None:
        filter_list.append('genre_of_game.id_game=%s')
        filter_args.append(id_game)

    if id_genre is not None:
        filter_list.append('genre_of_game.id_genre=%s')
        filter_args.append(id_genre)

    if filter_list:
        query += ' WHERE ' + ' AND '.join(filter_list)

    try:
        with connection.cursor() as cursor:
            if filter_list:
                cursor.execute(query, tuple(filter_args))
            else:
                cursor.execute(query)
            genres_of_games = cursor.fetchall()

        column_names = ['id_game', 'id_genre', 'game_name', 'genre_name']
        genres_of_games_dict = []

        for genre_of_game in genres_of_games:
            temp_dict = {}
            for key, value in zip(column_names, genre_of_game):
                temp_dict[key] = value
            genres_of_games_dict.append(temp_dict)

        return genres_of_games_dict
    finally:
        connection.close()


def add_genre_of_game(id_game, id_genre):
    connection = get_connection()
    query = "INSERT INTO genre_of_game (id_game, id_genre) VALUES (%s, %s)"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game, id_genre))
        connection.commit()
    finally:
        connection.close()


def delete_genre_of_game(id_game, id_genre):
    connection = get_connection()
    query = "DELETE FROM genre_of_game WHERE id_game = %s AND id_genre = %s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game, id_genre))
        connection.commit()
    finally:
        connection.close()


def get_list(id_game=None, id_user=None):
    connection = get_connection()
    query = '''SELECT list.id_game, list.id_user, list.list_type, list.rated, game.game_name, users.username
    FROM list
    JOIN users ON list.id_user = users.id_user
    JOIN game ON list.id_game = game.id_game'''

    filter_list = []
    filter_args = []

    if id_game is not None:
        filter_list.append("list.id_game = %s")
        filter_args.append(id_game)

    if id_user is not None:
        filter_list.append("list.id_user = %s")
        filter_args.append(id_user)

    if filter_list:
        query += ' WHERE ' + ' AND '.join(filter_list)

    try:
        with connection.cursor() as cursor:
            if filter_list:
                cursor.execute(query, tuple(filter_args))
            else:
                cursor.execute(query)
            user_lists = cursor.fetchall()

        column_names = ['id_game', 'id_user', 'list_type', 'rated', 'game_name', 'username']
        lists_dict = []

        for user_list in user_lists:
            temp_dict = {}
            for key, value in zip(column_names, user_list):
                temp_dict[key] = value
                if key == 'rated' and value is not None:
                    temp_dict[key] = int(value)
            lists_dict.append(temp_dict)

        return lists_dict
    finally:
        connection.close()


def add_list(id_game, id_user, list_type, rated=None):
    connection = get_connection()
    query = '''INSERT INTO list (id_game, id_user, list_type, rated) 
    VALUES (%s, %s, %s, %s)'''

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game, id_user, list_type, rated))
        connection.commit()
    finally:
        connection.close()


def update_list(id_game, id_user, list_type, rated=None):
    connection = get_connection()
    query = "UPDATE list SET list_type=%s, rated=%s WHERE id_game=%s AND id_user=%s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (list_type, rated, id_game, id_user))
        connection.commit()
    finally:
        connection.close()


def delete_list(id_game, id_user):
    connection = get_connection()
    query = "DELETE FROM list WHERE id_game=%s AND id_user=%s"

    try:
        with connection.cursor() as cursor:
            cursor.execute(query, (id_game, id_user))
        connection.commit()
    finally:
        connection.close()
