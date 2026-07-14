# flaskr/blog.py
from flask import Blueprint, render_template, session, redirect, url_for, flash, request

bp = Blueprint('blog', __name__)  # Sem url_prefix: será a raiz '/'

@bp.route('/')
def index():
    # Simulação de posts (na Aula 4 isso virá do SQLite)
    posts = [
        {'id': 1, 'title': 'Primeiro Post', 'body': 'Bem-vindo ao Flaskr!'},
        {'id': 2, 'title': 'Segundo Post', 'body': 'Blueprints são incríveis.'},
    ]
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=['GET', 'POST'])
def create():
    # Proteção simples: exige "login" (simulado via sessão)
    if 'user_id' not in session:
        flash('Você precisa estar logado para criar posts.', 'error')
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        # Na Aula 4, aqui salvaremos no SQLite
        flash('Post criado com sucesso! (simulado)', 'success')
        return redirect(url_for('blog.index'))
        
    return "<h1>Formulário de criação de post (A construir na Aula 4)</h1>"