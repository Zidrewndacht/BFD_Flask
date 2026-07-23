# Flask: Guia de Referência Rápida (Cheat Sheet)

Este documento é um índice prático e direto de todas as ferramentas do Flask abordadas no curso. Use-o para consultar **como** implementar cada funcionalidade no seu dia a dia.

📚 **Documentação Oficial:** [Flask Stable Docs](https://flask.palletsprojects.com/en/stable/)

---

## 1. O Core: Aplicação e Rotas

### `Flask` (A Instância)
**O que faz:** Cria o objeto WSGI que representa a sua aplicação web.
**Para que é útil:** É o ponto central onde rotas, configurações e blueprints são registrados.
**Implementação:**
```python
from flask import Flask
app = Flask(__name__) # __name__ diz ao Flask onde buscar templates e static
```

### `@app.route` / `@bp.route` (Roteamento)
**O que faz:** Mapeia uma URL para uma função Python (view function).
**Para que é útil:** Define quais URLs a aplicação responde e como extrair variáveis da URL.
**Implementação:**
```python
@app.route('/user/<int:id>')  # Conversor <int:> garante que id seja número
def ver_usuario(id):
    return f"Usuário {id}"

@app.route('/login', methods=['GET', 'POST']) # Restringe métodos HTTP
def login():
    pass
```
**Detalhes:** Conversores disponíveis: `string` (padrão), `int`, `float`, `path` (aceita `/`), `uuid`.
📚 *Ref: [Routing](https://flask.palletsprojects.com/en/stable/quickstart/#routing)*

### `url_for` (Construção de URLs)
**O que faz:** Gera URLs dinamicamente a partir do nome da função (endpoint).
**Para que é útil:** Evita URLs hardcoded. Se a rota mudar, o link atualiza automaticamente.
**Implementação:**
```python
from flask import url_for
# Em Python:
url = url_for('ver_usuario', id=42) # Gera '/user/42'
# Em Templates HTML:
# <a href="{{ url_for('static', filename='style.css') }}">
```

---

## 2. Request e Response

### `request` (O Objeto de Requisição)
**O que faz:** Contém todos os dados enviados pelo cliente na requisição atual.
**Para que é útil:** Ler formulários, parâmetros de URL, headers e método HTTP.
**Implementação:**
```python
from flask import request

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    if request.method == 'POST':
        dados_form = request.form.get('campo') # Dados do body (formulário)
    else:
        dados_url = request.args.get('q')      # Dados da URL (?q=...)
```
**Detalhes:** É um *Context Local*. Você o importa e usa, e o Flask garante que ele contém os dados da requisição da thread atual.
📚 *Ref: [Request Object](https://flask.palletsprojects.com/en/stable/api/#flask.Request)*

### Retornos e Status HTTP
**O que faz:** Define o que o servidor devolve ao navegador.
**Para que é útil:** Retornar HTML, JSON automático ou códigos de erro/sucesso.
**Implementação:**
```python
# 1. String (HTML/Texto) - Status 200 OK
return "<h1>Olá</h1>"

# 2. Dicionário/Lista (JSON Automático) - Status 200 OK
return {"status": "ok", "id": 1}

# 3. Tupla (Controle de Status Code)
return {"erro": "Não encontrado"}, 404
return "Criado com sucesso", 201
```

### `redirect` e `abort`
**O que faz:** `redirect` envia o cliente para outra URL. `abort` encerra a requisição com um erro HTTP.
**Implementação:**
```python
from flask import redirect, abort, url_for

return redirect(url_for('index')) # Redireciona (HTTP 302)
abort(404)                        # Levanta exceção HTTP 404
abort(403, "Acesso negado")       # Levanta exceção HTTP 403
```

---

## 3. Frontend: Templates e Static

### `render_template` (Jinja2)
**O que faz:** Carrega um arquivo HTML da pasta `templates/` e injeta variáveis Python nele.
**Implementação:**
```python
from flask import render_template

return render_template('perfil.html', usuario=nome, idade=30)
```
**Sintaxe Jinja2 no HTML:**
- `{{ variavel }}` : Imprime o valor (com escape automático contra XSS).
- `{% if condicao %} ... {% endif %}` : Controle de fluxo.
- `{% for item in lista %} ... {% endfor %}` : Loops.
📚 *Ref: [Templates](https://flask.palletsprojects.com/en/stable/quickstart/#rendering-templates)*

### Herança de Templates (`extends` e `block`)
**O que faz:** Permite criar um layout base (`base.html`) e preencher "buracos" nas páginas filhas.
**Implementação (`base.html`):**
```html
<title>{% block title %}Padrão{% endblock %}</title>
<main>{% block content %}{% endblock %}</main>
```
**Implementação (`filho.html`):**
```html
{% extends 'base.html' %}
{% block title %}Página Específica{% endblock %}
{% block content %}<h1>Conteúdo</h1>{% endblock %}
```

### Arquivos Estáticos (`static/`)
**O que faz:** Serve CSS, JS e Imagens da pasta `static/`.
**Implementação:**
```html
<!-- No HTML, NUNCA hardcode o caminho. Use url_for: -->
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

---

## 4. Estado: Sessão e Flash Messages

### `session` (Persistência entre Requests)
**O que faz:** Um dicionário que salva dados no navegador via cookie assinado criptograficamente.
**Para que é útil:** Manter o usuário logado ou lembrar preferências entre páginas.
**Implementação:**
```python
from flask import session

app.secret_key = 'chave_super_secreta' # OBRIGATÓRIO para a sessão funcionar

# Escrever
session['user_id'] = 42 

# Ler
user_id = session.get('user_id') 

# Limpar
session.clear()
```
📚 *Ref: [Sessions](https://flask.palletsprojects.com/en/stable/api/#flask.session)*

### `flash` e `get_flashed_messages`
**O que faz:** Envia uma mensagem de feedback que sobrevive a exatamente **um** redirecionamento.
**Para que é útil:** Exibir "Login realizado com sucesso!" ou "Erro no formulário" após um POST/Redirect/GET.
**Implementação (Python):**
```python
from flask import flash, redirect, url_for

flash('Erro: Senha inválida', 'error') # Categoria 'error' ajuda no CSS
return redirect(url_for('login'))
```
**Implementação (HTML `base.html`):**
```html
{% with messages = get_flashed_messages(with_categories=true) %}
  {% for category, msg in messages %}
    <div class="alert alert-{{ category }}">{{ msg }}</div>
  {% endfor %}
{% endwith %}
```
📚 *Ref: [Message Flashing](https://flask.palletsprojects.com/en/stable/patterns/flashing/)*

---

## 5. Arquitetura: Factory e Blueprints

### Application Factory (`create_app`)
**O que faz:** Encapsula a criação da instância `Flask` dentro de uma função.
**Para que é útil:** Evita imports circulares, permite múltiplas instâncias (ex: para testes) e configurações dinâmicas.
**Implementação (`__init__.py`):**
```python
import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev', DATABASE='...')
    
    from . import auth
    app.register_blueprint(auth.bp)
    
    return app
```
📚 *Ref: [App Factories](https://flask.palletsprojects.com/en/stable/patterns/appfactories/)*

### `Blueprint` (Modularização)
**O que faz:** Cria "mini-aplicações" que agrupam rotas de um mesmo domínio (ex: auth, blog).
**Para que é útil:** Organizar projetos grandes em múltiplos arquivos `.py`.
**Implementação (`auth.py`):**
```python
from flask import Blueprint

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    return "Login"
```
**Registro na Factory:**
```python
app.register_blueprint(auth.bp)
```
**Mudança no `url_for`:** O endpoint ganha o prefixo do blueprint: `url_for('auth.login')`.
📚 *Ref: [Blueprints](https://flask.palletsprojects.com/en/stable/blueprints/)*

---

## 6. Banco de Dados (SQLite) e CLI

### `g` e `current_app` (Contexto de Aplicação)
**O que faz:** `g` armazena dados durante *um único request* (ex: conexão com o BD). `current_app` aponta para a app que está rodando.
**Implementação (`db.py`):**
```python
import sqlite3
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row # Acesso por nome de coluna
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
```

### `teardown_appcontext` e `cli.add_command`
**O que faz:** Registra funções para rodar automaticamente no fim do request ou cria comandos de terminal customizados.
**Implementação:**
```python
import click

@click.command('init-db')
def init_db_command():
    """Limpa e cria as tabelas."""
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
    click.echo('Banco inicializado.')

def init_app(app):
    app.teardown_appcontext(close_db)      # Chama close_db ao fim de cada request
    app.cli.add_command(init_db_command)   # Cria o comando: flask init-db
```
📚 *Ref: [Tutorial DB](https://flask.palletsprojects.com/en/stable/tutorial/database/) e [CLI](https://flask.palletsprojects.com/en/stable/cli/)*

---

## 7. Autenticação e Decoradores

### Hash de Senhas (`werkzeug.security`)
**O que faz:** Criptografa senhas de forma segura (nunca salve texto puro).
**Implementação:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# No Registro:
hash_senha = generate_password_hash('senha123')
db.execute("INSERT INTO user (senha) VALUES (?)", (hash_senha,))

# No Login:
user = db.execute('SELECT * FROM user WHERE nome = ?', (nome,)).fetchone()
if not check_password_hash(user['senha'], 'senha123'):
    abort(403) # Senha incorreta
```

### `before_app_request`
**O que faz:** Executa uma função *antes* de qualquer view do blueprint/app ser chamada.
**Para que é útil:** Carregar o usuário logado do banco e deixar disponível em `g.user`.
**Implementação:**
```python
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
```

### Decorador Customizado (`@login_required`)
**O que faz:** Protege rotas, exigindo que `g.user` exista.
**Para que é útil:** Evita repetir `if not g.user: return redirect...` em toda rota protegida.
**Implementação:**
```python
import functools

def login_required(view):
    @functools.wraps(view) # Preserva o nome original da função para o url_for
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs) # Chama a rota original
    return wrapped_view

# Uso:
@bp.route('/create')
@login_required
def create():
    pass
```
