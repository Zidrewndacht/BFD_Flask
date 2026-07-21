# flaskr/db.py
import sqlite3
import click
from flask import current_app, g

def get_db():
    """Abre uma nova conexão com o banco, se não existir uma para o request atual."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        # Configurações que você já conhece da aula de BD!
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")

    return g.db

def close_db(e=None):
    """Fecha a conexão no final do request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Lê o schema.sql e cria as tabelas."""
    db = get_db()
    # open_resource abre um arquivo relativo ao pacote flaskr/
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

@click.command('init-db')
def init_db_command():
    """Comando CLI para limpar e recriar o banco."""
    init_db()
    click.echo('Banco de dados inicializado com sucesso.')

def init_app(app):
    """Registra as funções de banco na aplicação."""
    app.teardown_appcontext(close_db) # Garante que a conexão feche ao fim do request
    app.cli.add_command(init_db_command) # Adiciona o comando 'flask init-db'