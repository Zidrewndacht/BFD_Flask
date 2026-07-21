# flaskr/blog.py
from flask import Blueprint, flash, g, redirect, render_template, request, url_for, abort
from werkzeug.exceptions import abort
from .auth import login_required
from .db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Título é obrigatório.'

        if error is not None:
            flash(error, 'error')
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)',
                (title, body, g.user['id'])
            )
            db.commit()
            flash('Post criado com sucesso!', 'success')
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    """Função auxiliar para buscar um post e garantir que ele existe."""
    post = get_db().execute(
        'SELECT p.id, title, body, created, author_id, username'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} não existe.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403) # Forbidden

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Título é obrigatório.'

        if error is not None:
            flash(error, 'error')
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            flash('Post atualizado!', 'success')
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id) # Garante que o post existe e o usuário é o autor
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    flash('Post deletado.', 'success')
    return redirect(url_for('blog.index'))