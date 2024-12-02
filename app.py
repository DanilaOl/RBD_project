import hashlib

from flask import Flask, request, render_template, session, redirect, url_for, flash
from flask.sessions import SessionMixin

import db_service

app = Flask(__name__)
app.secret_key = 'myMegaSecretKey'


def get_session_user(_session: SessionMixin):
    if not _session.get('user'):
        _session['user'] = {}

    return _session['user']

@app.route('/')
def games():
    user = get_session_user(session)

    parameters = dict(request.args)
    if 'id_developer' in parameters and parameters['id_developer'] == 'none':
        parameters.pop('id_developer')

    if 'id_publisher' in parameters and parameters['id_publisher'] == 'none':
        parameters.pop('id_publisher')

    if 'search_text' in parameters and parameters['search_text'] == '':
        parameters.pop('search_text')

    if not parameters:
        all_games = db_service.get_all_games()
    else:
        all_games = db_service.get_all_games(**parameters)

    all_developers = db_service.get_all_developers()
    all_publishers = db_service.get_all_publishers()

    return render_template(
        'games/games.html',
        games=all_games, user=user,
        developers=all_developers, publishers=all_publishers
    )


@app.route('/games/<int:id_game>', methods=['GET', 'POST'])
def game_detail(id_game):
    session_user = get_session_user(session)

    game = db_service.get_game(id_game)
    games_genres = db_service.get_genre_of_game(id_game=id_game)
    comments = db_service.get_comments(id_game=id_game)

    user_game_list = None

    if session_user and session_user['role'] != 'admin':
        user_game_list = db_service.get_list(id_game, session_user['id_user'])
        if user_game_list:
            user_game_list = user_game_list[0]
        else:
            user_game_list = None

    return render_template(
        'games/game.html',
        game=game, user_game_list=user_game_list,
        user=session_user, genres=games_genres, comments=comments
    )


@app.route('/games/<int:id_game>/delete')
def delete_game(id_game):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash(
            'Вы должны быть администратором, чтобы удалить игру',
            category='error'
        )
        return redirect(url_for('game_detail', id_game=id_game))

    try:
        db_service.delete_game(id_game)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
    else:
        flash('Игра успешно удалена', 'success')

    return redirect(url_for('games'))


@app.route('/games/<int:id_game>/update', methods=['GET', 'POST'])
def update_game(id_game):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash(
            'Вы должны быть администратором, '
            'чтобы обновить информацию об игре',
            category='error'
        )
        return redirect(url_for('games'))

    if request.method == 'POST':
        game_name = request.form['game_name']
        game_description = request.form['game_description']
        game_release_date = request.form['game_release_date']
        game_developer_id = request.form['game_developer']
        game_publisher_id = request.form['game_publisher']
        new_game_genres_ids = request.form.getlist('genres')
        new_game_genres_ids = [int(genre_id) for genre_id in new_game_genres_ids]

        if game_description == '':
            game_description = None

        if game_publisher_id == 'none':
            game_publisher_id = None

        current_game_genres = db_service.get_genre_of_game(id_game=id_game)
        current_game_genres_ids = [genre['id_genre'] for genre in current_game_genres]

        genres_to_add = list(set(new_game_genres_ids) - set(current_game_genres_ids))
        genres_to_remove = list(set(current_game_genres_ids) - set(new_game_genres_ids))

        for to_add in genres_to_add:
            db_service.add_genre_of_game(id_game, to_add)

        for to_remove in genres_to_remove:
            db_service.delete_genre_of_game(id_game, to_remove)

        try:
            db_service.update_game(
                id_game, game_name, game_description, game_release_date,
                game_publisher_id, game_developer_id
            )
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('update_game', id_game=id_game))
        else:
            flash('Информация об игре успешно обновлена', 'success')
            return redirect(url_for('game_detail', id_game=id_game))

    game = db_service.get_game(id_game)
    all_publishers = db_service.get_all_publishers()
    all_developers = db_service.get_all_developers()
    games_genres = db_service.get_genre_of_game(id_game=id_game)
    all_genres = db_service.get_all_genres()
    games_genres_ids = [genre['id_genre'] for genre in games_genres]

    return render_template(
        'games/create_update_game.html',
        user=session_user,
        game=game,
        publishers=all_publishers,
        developers=all_developers,
        games_genres_ids=games_genres_ids,
        all_genres=all_genres,
        update=True
    )


@app.route('/games/create', methods=['GET', 'POST'])
def create_game():
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash(
            'Вы должны быть администратором, чтобы создать игру',
            category='error'
        )
        return redirect(url_for('games'))

    if request.method == 'POST':
        game_name = request.form['game_name']
        game_description = request.form['game_description']
        game_release_date = request.form['game_release_date']
        game_developer_id = request.form['game_developer']
        game_publisher_id = request.form['game_publisher']

        if game_description == '':
            game_description = None

        if game_publisher_id == 'none':
            game_publisher_id = None

        try:
            db_service.add_game(game_name, game_description, game_release_date, game_developer_id, id_publisher=game_publisher_id)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('create_game'))
        else:
            flash('Игра успешно создана', 'success')
            return redirect(url_for('games'))

    all_publishers = db_service.get_all_publishers()
    all_developers = db_service.get_all_developers()

    return render_template(
        'games/create_update_game.html',
        user=session_user, game=None, publishers=all_publishers,
        developers=all_developers, update=False
    )


@app.route('/users')
def users():
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash(
            'Вы должны быть администратором, чтобы видеть эту страницу',
            category='error'
        )
        return redirect(url_for('games'))

    all_users = db_service.get_all_users()

    return render_template(
        'users/users.html',
        user=session_user,
        users=all_users
    )


@app.route('/users/<int:id_user>')
def user_detail(id_user):
    session_user = session.get('user')
    user_info = db_service.get_user(id_user)

    user_lists = db_service.get_list(id_user=id_user)

    if user_lists is not None:

        categorized_user_lists = {'planned': [], 'playing': [],
                                  'postponed': [], 'completed': []}

        for user_list in user_lists:
            categorized_user_lists[user_list['list_type']].append(user_list)
    else:
        categorized_user_lists = None


    return render_template(
        'users/user.html',
        user=session_user,
        user_info=user_info,
        categorized_user_lists=categorized_user_lists
    )



@app.route('/users/<int:id_user>/update', methods=['GET', 'POST'])
def update_user(id_user):
    session_user = session.get('user')
    user_info = db_service.get_user(id_user)

    if request.method == 'POST':
        new_username = request.form['user_username']
        new_email = request.form['user_email']
        old_password = request.form['old_password']

        if old_password == '':
            try:
                db_service.update_user(id_user, username=new_username,
                                       email=new_email)
            except Exception as e:
                flash('Что-то пошло не так', 'error')
                return redirect(url_for('update_user', id_user=id_user))
            else:
                session['user']['username'] = new_username
                flash('Данные успешно обновлены', 'success')
                return redirect(url_for('user_detail', id_user=id_user))
        else:
            old_password_hash = (hashlib.sha256(old_password.encode('utf-8'))
                                 .hexdigest().upper())

            if old_password_hash != user_info['password']:
                flash('Вы ввели неверный пароль', 'error')
                return redirect(url_for('update_user',
                                        id_user=id_user))

            new_password = request.form['new_password']
            new_password_repeat = request.form['new_password_repeat']

            if new_password != new_password_repeat:
                flash('Новые пароли не совпадают', 'error')
                return redirect(url_for('update_user',
                                        id_user=id_user))

            password = new_password

            try:
                db_service.update_user(id_user, username=new_username,
                                       password=password, email=new_email)
            except Exception:
                flash('Что-то пошло не так', 'error')
                return redirect(url_for('update_user',
                                        id_user=id_user))
            else:
                session['user']['username'] = new_username
                flash('Данные успешно обновлены', 'success')
                return redirect(url_for('user_detail',
                                        id_user=id_user))

    if session_user and (session_user['id_user'] == id_user):
        return render_template(
            'users/update_user.html',
            user=session.get('user'),
            user_info=user_info,
            update=True
        )

    flash('Вы не можете изменять данные этого пользователя',
          category='error')
    return redirect(url_for('login'))


@app.route('/users/<int:id_user>/delete', methods=['GET', 'POST'])
def delete_user(id_user):
    session_user = get_session_user(session)
    if not session_user:
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('user_detail', id_user=id_user))

    if session_user['role'] != 'admin' and session_user['id_user'] != id_user:
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('user_detail', id_user=id_user))

    try:
        db_service.delete_user(id_user)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
        return redirect(url_for('user_detail', id_user=id_user))
    else:
        flash('Пользователь успешно удалён', 'success')

        if session_user['role'] == 'admin':
            return redirect(url_for('users'))
        else:
            session['user'] = {}
            return redirect(url_for('games'))


@app.route('/developers')
def developers():
    session_user = get_session_user(session)
    all_developers = db_service.get_all_developers()

    return render_template(
        'developers/developers.html',
        user=session_user, developers=all_developers
    )


@app.route('/developers/<int:id_developer>')
def developer_detail(id_developer):
    session_user = get_session_user(session)
    developer = db_service.get_developer(id_developer)
    developer_games = db_service.get_all_games(id_developer=id_developer)

    return render_template(
        'developers/developer.html',
        user=session_user,
        developer=developer,
        games=developer_games
    )


@app.route('/developers/<int:id_developer>/delete')
def delete_developer(id_developer):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('developer_detail',
                                id_developer=id_developer))

    try:
        db_service.delete_developer(id_developer)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
        return redirect(url_for('developer_detail',
                                id_developer=id_developer))
    else:
        flash('Разработчик удалён', 'success')
        return redirect(url_for('developers'))


@app.route('/developers/<int:id_developer>/update', methods=['GET', 'POST'])
def update_developer(id_developer):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('developer_detail',
                                id_developer=id_developer))

    if request.method == 'POST':
        studio_name = request.form['studio_name']
        country = request.form['country']

        if country == '':
            country = None

        try:
            db_service.update_developer(id_developer, studio_name, country)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('update_developer',
                                    id_developer=id_developer))
        else:
            flash('Информация о разработчике успешно обновлена', 'success')
            return redirect(url_for('developer_detail',
                                    id_developer=id_developer))

    developer = db_service.get_developer(id_developer)

    return render_template(
        'developers/create_update_developer.html',
        user=session_user, developer=developer, update=True
    )


@app.route('/developers/create', methods=['GET', 'POST'])
def create_developer():
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('developers'))

    if request.method == 'POST':
        studio_name = request.form['studio_name']
        country = request.form['country']

        if country == '':
            country = None

        try:
            db_service.add_developer(studio_name, country)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('create_developer'))
        else:
            flash('Разработчик создан', 'success')
            return redirect(url_for('developers'))

    return render_template(
        'developers/create_update_developer.html',
        user=session_user, developer=None, update=False
    )


@app.route('/publishers')
def publishers():
    session_user = get_session_user(session)
    all_publishers = db_service.get_all_publishers()

    return render_template(
        'publishers/publishers.html',
        user=session_user, publishers=all_publishers
    )


@app.route('/publishers/<int:id_publisher>')
def publisher_detail(id_publisher):
    session_user = get_session_user(session)
    publisher = db_service.get_publisher(id_publisher)
    publisher_games = db_service.get_all_games(id_publisher=id_publisher)

    return render_template(
        'publishers/publisher.html',
        user=session_user, publisher=publisher,
        games=publisher_games
    )


@app.route('/publishers/<int:id_publisher>/delete')
def delete_publisher(id_publisher):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('publisher_detail',
                                id_publisher=id_publisher))

    try:
        db_service.delete_publisher(id_publisher)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
        return redirect(url_for('publisher_detail',
                                id_publisher=id_publisher))
    else:
        flash('Издатель удалён', 'success')
        return redirect(url_for('publishers'))


@app.route('/publishers/<int:id_publisher>/update', methods=['GET', 'POST'])
def update_publisher(id_publisher):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('publisher_detail',
                                id_publisher=id_publisher))

    if request.method == 'POST':
        publisher_name = request.form['publisher_name']
        country = request.form['country']

        if country == '':
            country = None

        try:
            db_service.update_publisher(id_publisher, publisher_name, country)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('update_publisher',
                                    id_publisher=id_publisher))
        else:
            flash('Информация об издателе успешно обновлена', 'success')
            return redirect(url_for('publisher_detail',
                                    id_publisher=id_publisher))

    publisher = db_service.get_publisher(id_publisher)

    return render_template(
        'publishers/create_update_publisher.html',
        user=session_user, publisher=publisher, update=True
    )


@app.route('/publishers/create', methods=['GET', 'POST'])
def create_publisher():
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('publishers'))

    if request.method == 'POST':
        publisher_name = request.form['publisher_name']
        country = request.form['country']

        if country == '':
            country = None

        try:
            db_service.add_publisher(publisher_name, country)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('create_publisher'))
        else:
            flash('Издатель создан', 'success')
            return redirect(url_for('publishers'))

    return render_template(
        'publishers/create_update_publisher.html',
        user=session_user, publisher=None, update=False
    )


@app.route('/genres')
def genres():
    all_genres = db_service.get_all_genres()
    return render_template(
        'genres/genres.html',
        user=session.get('user', None),
        genres=all_genres
    )


@app.route('/genres/<int:id_genre>')
def genre_detail(id_genre):
    session_user = get_session_user(session)
    genre = db_service.get_genre(id_genre)
    games_with_genre = db_service.get_genre_of_game(id_genre=id_genre)

    return render_template(
        'genres/genre.html',
        user=session_user, genre=genre,
        games=games_with_genre
    )


@app.route('/genres/<int:id_genre>/delete')
def delete_genre(id_genre):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('genre_detail', id_genre=id_genre))

    try:
        db_service.delete_genre(id_genre)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
        return redirect(url_for('genre_detail', id_genre=id_genre))
    else:
        flash('Жанр удалён', 'success')
        return redirect(url_for('genres'))


@app.route('/genres/<int:id_genre>/update', methods=['GET', 'POST'])
def update_genre(id_genre):
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('genre_detail', id_genre=id_genre))

    if request.method == 'POST':
        genre_name = request.form['genre_name']

        try:
            db_service.update_genre(id_genre, genre_name)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('update_genre', id_genre=id_genre))
        else:
            flash('Информация о жанре успешно обновлена', 'success')
            return redirect(url_for('genre_detail', id_genre=id_genre))

    genre = db_service.get_genre(id_genre)

    return render_template(
        'genres/create_update_genre.html',
        user=session_user, genre=genre, update=True
    )


@app.route('/genres/create', methods=['GET', 'POST'])
def create_genre():
    session_user = get_session_user(session)

    if not session_user or session_user['role'] != 'admin':
        flash('Вам недоступна эта операция', 'error')
        return redirect(url_for('genres'))

    if request.method == 'POST':
        genre_name = request.form['genre_name']

        try:
            db_service.add_genre(genre_name)
        except Exception as e:
            flash('Что-то пошло не так', 'error')
            return redirect(url_for('create_genre'))
        else:
            flash('Жанр создан', 'success')
            return redirect(url_for('genres'))

    return render_template(
        'genres/create_update_genre.html',
        user=session_user, genre=None, update=False
    )


@app.route('/lists/<int:id_game>_<int:id_user>/delete')
def delete_list(id_game, id_user):
    try:
        db_service.delete_list(id_game, id_user)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
    else:
        flash('Игра удалена из списка', 'success')
    return redirect(url_for('game_detail', id_game=id_game))


@app.route('/lists/<int:id_game>_<int:id_user>/update', methods=['POST'])
def update_list(id_game, id_user):
    session_user = get_session_user(session)

    if not session_user:
        flash('Вы должны быть авторизованы, чтобы обновить списки', 'error')
        return redirect(url_for('game_detail', id_game=id_game))

    if session_user['role'] == 'admin':
        flash('Администраторам не позволяется добавлять игры в списки')
        return redirect(url_for('game_detail', id_game=id_game))

    list_type = request.form['list_type']

    if list_type == 'delete':
        return redirect(url_for('delete_list',
                                id_game=id_game, id_user=id_user))

    rated = request.form['rated']

    if rated == 'none':
        rated = None

    list_item = db_service.get_list(id_game, id_user)

    try:
        if not list_item:
            db_service.add_list(id_game, id_user, list_type, rated)
        else:
            db_service.update_list(id_game, id_user, list_type, rated)

    except Exception as e:
        flash('Что-то пошло не так', 'error')
    else:
        flash('Список обновлён', 'success')
    return redirect(url_for('game_detail', id_game=id_game))


@app.route('/comments/<int:id_game>_<int:id_user>/create', methods=['POST'])
def create_comment(id_game, id_user):
    session_user = get_session_user(session)

    if not session_user:
        flash('Вы должны быть авторизованы, чтобы оставить комментарий', 'error')
        return redirect(url_for('game_detail', id_game=id_game))

    if session_user['role'] == 'admin':
        flash('Администраторам не позволяется оставлять комментарии')
        return redirect(url_for('game_detail', id_game=id_game))

    comment_text = request.form['comment_text']

    existing_comment = db_service.get_comments(id_game, id_user)

    if existing_comment:
        flash('Правилами сайта запрещено оставлять более одного комментария для игры', 'error')
        return redirect(url_for('game_detail', id_game=id_game))

    try:
        db_service.add_comment(id_game, id_user, comment_text)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
    else:
        flash('Комментарий добавлен', 'success')

    return redirect(url_for('game_detail', id_game=id_game))


@app.route('/comments/<int:id_game>_<int:id_user>/delete')
def delete_comment(id_game, id_user):
    session_user = get_session_user(session)

    if not session_user:
        flash('Вы должны быть авторизованы', 'error')
        return redirect(url_for('game_detail', id_game=id_game))

    if session_user['role'] != 'admin' and session_user['id_user'] != id_user:
        flash('Вам нельзя удалить чужой комментарий', 'error')
        return redirect(url_for('game_detail', id_game=id_game))

    try:
        db_service.delete_comment(id_game, id_user)
    except Exception as e:
        flash('Что-то пошло не так', 'error')
    else:
        flash('Комментарий удалён', 'success')

    return redirect(url_for('game_detail', id_game=id_game))



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_user = db_service.validate_user(username, password)

        if db_user:
            session['user'] = {}
            session['user']['id_user'] = db_user['id_user']
            session['user']['username'] = db_user['username']
            session['user']['role'] = 'user'
            flash(f'Добро пожаловать {db_user["username"]}', 'success')
            return redirect(url_for('games'))
        else:
            flash('Неверные логин/пароль', 'error')
            return redirect(url_for('login'))

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session['user'] = {}
    flash('Вы успешно вышли из аккаунта', 'success')
    return redirect(url_for('games'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_repeat = request.form['password_repeat']

        if password != password_repeat:
            flash('Пароли не совпадают', 'error')
            return redirect(url_for('register'))

        try:
            db_service.add_user(username, password, email)
        except Exception as e:
            flash('Аккаунт уже существует', 'error')
            return redirect(url_for('register'))
        else:
            flash('Вы успешно зарегистрировались', 'success')
            return redirect(url_for('login'))

    return render_template('auth/register.html')


@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db_admin = db_service.validate_admin(username, password)

        if db_admin:
            session['user'] = {}
            session['user']['id_user'] = db_admin['id']
            session['user']['username'] = db_admin['login']
            session['user']['role'] = 'admin'
            flash(
                f'Добро пожаловать, администратор {db_admin["login"]}',
                category='success'
            )
            return redirect(url_for('games'))
        else:
            flash('Неверные логин/пароль', 'error')
            return redirect(url_for('admin_login'))

    return render_template('auth/login.html')

if __name__ == '__main__':
    app.run(debug=False)
