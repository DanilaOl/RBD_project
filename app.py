from flask import Flask, request, render_template, session

import db_service

app = Flask(__name__)
app.secret_key = 'myMegaSecretKey'


@app.route('/games')
def games():
    parameters = request.args
    if not parameters:
        all_games = db_service.get_all_games()
    else:
        all_games = db_service.get_all_games(**parameters)
    session['role'] = 'admin'
    return render_template('games/games.html', games=all_games, session=session)


@app.route('/games/<int:id_game>')
def game_detail(id_game):
    return "asdf"


@app.route('/games/<int:id_game>/delete')
def delete_game(id_game):
    return 'asdf'


@app.route('/developers')
def developers():
    return render_template('developers/developers.html', session=session)


@app.route('/publishers')
def publishers():
    return render_template('publishers/publishers.html', session=session)


@app.route('/genres')
def genres():
    return render_template('genres/genres.html', session=session)


@app.route('/login')
def login():
    return render_template('auth/login.html', session=session)


if __name__ == '__main__':
    app.run(debug=True)
