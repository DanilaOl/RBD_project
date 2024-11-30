from flask import Flask, request, render_template, session, redirect, url_for, flash
# from flask_login import UserMixin, LoginManager, current_user, login_required, logout_user
# from flask_security import RoleMixin

import db_service

app = Flask(__name__)
app.secret_key = 'myMegaSecretKey'


@app.route('/games')
def games():
    parameters = dict(request.args)
    if 'id_developer' in parameters and parameters['id_developer'] == 'none':
        parameters.pop('id_developer')

    if 'id_publisher' in parameters and parameters['id_publisher'] == 'none':
        parameters.pop('id_publisher')

    if not parameters:
        all_games = db_service.get_all_games()
    else:
        all_games = db_service.get_all_games(**parameters)

    all_developers = db_service.get_all_developers()
    all_publishers = db_service.get_all_publishers()

    return render_template(
        'games/games.html',
        games=all_games, user=session.get('user', None),
        developers=all_developers, publishers=all_publishers
    )


@app.route('/games/<int:id_game>', methods=['GET', 'POST'])
def game_detail(id_game):
    if request.method == 'POST':
        list_type = request.form['list_type']

        if list_type == 'delete':
            return redirect(url_for(
                'delete_list',
                id_game=id_game,
                id_user=session.get('user')['id_user']
            ))

        rated = request.form['rated']
        user = session.get('user')

        if rated == 'none':
            rated = None

        list_item = db_service.get_list(id_game, user['id_user'])

        if not list_item:
            db_service.add_list(id_game, user['id_user'], list_type, rated)
        else:
            db_service.update_list(id_game, user['id_user'], list_type, rated)

        return redirect(url_for('game_detail', id_game=id_game))

    game = db_service.get_game(id_game)
    user_game_list = None

    if session.get('user') and session.get('user')['role'] != 'admin':
        session_user = session['user']
        user_game_list = db_service.get_list(id_game, session_user['id_user'])
        if user_game_list:
            user_game_list = user_game_list[0]
        else:
            user_game_list = None

    return render_template(
        'games/game.html',
        game=game, user_game_list=user_game_list,
        user=session.get('user', None),
    )


@app.route('/games/<int:id_game>/delete')
def delete_game(id_game):
    user = session.get('user')

    if not user or user['role'] != 'admin':
        return redirect(url_for('game_detail', id_game=id_game))

    return 'asdf'


@app.route('/users/<int:id_user>')
def current_user(id_user):
    session_user = session.get('user')
    user_info = db_service.get_user(id_user)

    if session_user and (session_user['id_user'] == id_user
                         or session_user['role'] == 'admin'):
        return render_template(
            'users/user.html',
            user=session.get('user'),
            user_info=user_info,
        )

    return redirect(url_for('login'))


@app.route('/users/<int:id_user>/update', methods=['GET', 'POST'])
def update_user(id_user):
    session_user = session.get('user')
    user_info = db_service.get_user(id_user)

    if session_user and (session_user['id_user'] == id_user
                         or session_user['role'] == 'admin'):
        return render_template(
            'users/update_user.html',
            user=session.get('user'),
            user_info=user_info,
            update=True
        )
    
    return redirect(url_for('login'))


@app.route('/users/<int:id_user>/delete', methods=['GET', 'POST'])
def delete_user(id_user):
    session_user = session.get('user')

    if session_user and (session_user['id_user'] == id_user
                         or session_user['role'] == 'admin'):
        db_service.delete_user(id_user)
        flash('User deleted!', 'info')
    else:
        flash('You are not allowed to delete this user', 'danger')

    return redirect(url_for('games'))

@app.route('/developers')
def developers():
    all_developers = db_service.get_all_developers()

    return render_template(
        'developers/developers.html',
        user=session.get('user', None), developers=all_developers
    )


@app.route('/developers/<int:id_developer>')
def developer_detail(id_developer):
    return 'asdf'


@app.route('/developers/<int:id_developer>/delete')
def delete_developer(id_developer):
    return 'asdf'


@app.route('/publishers')
def publishers():
    all_publishers = db_service.get_all_publishers()
    return render_template(
        'publishers/publishers.html',
        user=session.get('user', None),
        publishers=all_publishers
    )


@app.route('/publishers/<int:id_publisher>')
def publisher_detail(id_publisher):
    return 'asdf'


@app.route('/publishers/<int:id_publisher>/delete')
def delete_publisher(id_publisher):
    return 'asdf'


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
    genre = db_service.get_genre(id_genre)
    games_with_genre = db_service.get_genre_of_game(id_genre)
    return render_template(
        'genres/'
    )


@app.route('/genres/<int:id_genre>/delete')
def delete_genre(id_genre):
    return 'asdf'


@app.route('/lists/<int:id_game>_<int:id_user>/delete')
def delete_list(id_game, id_user):
    db_service.delete_list(id_game, id_user)
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
            return redirect(url_for('games'))
        else:
            flash('Неверные логин/пароль', 'error')
            return redirect(url_for('login'))

    return render_template('auth/login.html')


@app.route('/logout')
def logout():
    session['user'] = {}
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
            db_service.add_user(username, email, password)
        except Exception:
            flash('Аккаунт уже существует', 'error')
            return redirect(url_for('register'))
        else:
            flash('Вы успешно зарегистрировались', 'info')
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
            return redirect(url_for('games'))
        else:
            flash('Неверные логин/пароль', 'error')
            return redirect(url_for('admin_login'))

    return render_template('auth/login.html')

if __name__ == '__main__':
    app.run(debug=False)
