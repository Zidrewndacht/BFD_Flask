# flaskr/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        # Validação simulada (sem BD por enquanto)
        if username == 'admin' and password == '123':
            session['user_id'] = 1
            session['username'] = username
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('blog.index'))
        else:
            flash('Usuário ou senha inválidos.', 'error')
            return redirect(url_for('auth.login'))
            
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('blog.index'))