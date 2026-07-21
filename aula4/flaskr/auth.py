# flaskr/auth.py
import functools
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash
from .db import get_db

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None

        if not username:
            error = 'Username é obrigatório.'
        elif not password:
            error = 'Password é obrigatório.'

        if error is None:
            try:
                db.execute(
                    "INSERT INTO user (username, password) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                db.commit()
            except db.IntegrityError:
                error = f"Usuário {username} já está registrado."
            else:
                flash('Cadastro realizado! Faça login.', 'success')
                return redirect(url_for('auth.login'))

        flash(error, 'error')
    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        
        user = db.execute('SELECT * FROM user WHERE username = ?', (username,)).fetchone()

        if user is None:
            error = 'Usuário incorreto.'
        elif not check_password_hash(user['password'], password):
            error = 'Senha incorreta.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))

        flash(error, 'error')
    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    """Roda ANTES de qualquer view. Carrega o usuário do banco no g."""
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('index'))

def login_required(view):
    """Decorador para proteger rotas que exigem login."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Você precisa estar logado para acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view