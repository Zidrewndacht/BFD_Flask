# Aula 4 — Persistência com SQLite e o CRUD Completo

Nas aulas anteriores, construímos a arquitetura do nosso projeto (Application Factory e Blueprints) usando dados em memória. Hoje, vamos conectar o Flask ao **SQLite** que você já domina da disciplina de Banco de Dados. 

---

## 1. O Módulo de Banco de Dados (`flaskr/db.py`)

No Flask, a conexão com o banco de dados não é global. Ela é criada no início de cada requisição (ou quando necessária) e fechada no fim. Para isso, usamos o objeto `g` (que armazena dados durante **um único request**) e `current_app` (que aponta para a aplicação que está rodando no momento).

<details>
<summary><strong>Por que g?</strong></summary>

## 1.1 O Problema: Por que não usar uma variável global do Python?

Imagine que nosso servidor Flask está rodando. O Python é uma linguagem que, por padrão, executa em um único processo. 
Se dois usuários, **Ana** e **Bruno**, acessam o blog exatamente ao mesmo tempo, o servidor web (Werkzeug/Gunicorn) usa *threads* (ou mecanismos assíncronos) para atender os dois simultaneamente.

Se usássemos uma variável global comum do Python para guardar o usuário logado, teríamos um desastre:

```python
usuario_atual = None 

@app.route('/login', methods=['POST'])
def login():
    global usuario_atual
    usuario_atual = buscar_usuario(request.form['username']) # Ana loga
    return redirect('/')

@app.route('/postar')
def postar():
    # E se o request do Bruno entrar nessa thread antes do post da Ana?
    # Bruno acaba postando como se fosse a Ana!
    salvar_post(author=usuario_atual) 
```

**Variáveis globais em Python são compartilhadas entre todos os usuários.** Elas são um vetor de segurança catastrófico e causam *race conditions* (condições de corrida).

## 1.2. A Solução do Flask: "Context Locals"

O Flask precisa de um lugar para guardar dados que sejam **globais para o código** (para que você não precise ficar passando o usuário como argumento em 15 funções diferentes: `def view(user, request, db...)`), mas que sejam **estritamente isolados por requisição** (o request da Ana não pode ver os dados do request do Bruno).

É aí que entra o objeto **`g`** (que historicamente significa *global*, mas na verdade é um *global de contexto de request*).

### A Analogia da Prancheta de Atendimento
Pense no `g` como uma **prancheta com um formulário em branco** que é entregue ao "atendente" (a thread do servidor) no exato milissegundo em que um request chega.

1. O request chega. O Flask cria uma prancheta `g` vazia e a entrega para a thread.
2. Várias funções são chamadas durante esse atendimento (hooks de segurança, a view function, o renderizador de template). **Todas elas podem olhar para a prancheta `g` e ler/escrever nela.**
3. O response é enviado para o navegador.
4. **A prancheta `g` é incinerada.** Ela deixa de existir.
5. No próximo request (mesmo que seja do mesmo usuário, 1 segundo depois), uma **nova** prancheta `g` vazia é criada.

---

## 1.3. O Ciclo de Vida do `g` no nosso Blog (Flaskr)

Vamos olhar para o código de autenticação que escrevemos e entender o *porquê* de cada linha:

```python
@bp.before_app_request
def load_logged_in_user():
    # 1. Olhamos o cookie (session) para ver se tem um ID
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None # A prancheta ganha uma anotação: "Ninguém logado"
    else:
        # 2. Vamos no SQLite buscar os dados FRESCOS do usuário
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone() # A prancheta ganha o dicionário com os dados do usuário
```

**Por que fazemos isso no `before_app_request`?**
Porque essa função roda *antes* de qualquer rota. Seja `/blog/create`, `/auth/logout` ou `/`, o Flask vai no banco, pega o usuário e "gruda" na prancheta `g`.

Quando a sua view function (rota) for executada logo em seguida, ela não precisa se preocupar em abrir o banco de dados de novo. Ela apenas olha para a prancheta:

```python
@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    # Eu preciso do ID do autor para salvar o post.
    # Em vez de fazer um SELECT no banco de novo, eu pego da prancheta!
    db.execute(
        'INSERT INTO post (title, body, author_id) VALUES (?, ?, ?)',
        (title, body, g.user['id']) # <--- Lendo da prancheta 'g'
    )
```

---

## 1.4. A Dúvida Clássica: "Por que não guardar o usuário direto na `session`?"

Se a `session` já lembra do usuário entre as telas, por que não fazemos `session['user'] = dados_do_usuario` no login e esquecemos o `g` e o banco de dados?

1. **Tamanho do Cookie:** A `session` do Flask é enviada para o navegador como um Cookie. Navegadores limitam cookies a ~4KB. Guardar objetos complexos, listas de permissões ou textos longos na session vai estourar o limite e quebrar a aplicação silenciosamente. Na `session`, guardamos **apenas o ID** (um simples número inteiro: `session['user_id'] = 1`).
2. **Dados "Stale" (Desatualizados):** Se a Ana mudar o nome de usuário dela no banco de dados, o cookie dela (a `session`) continuará com o nome antigo até ela fazer logout e login de novo. Usando o `g`, nós usamos o ID da session para buscar o usuário no SQLite **a cada request**. Isso garante que a aplicação sempre vê os dados mais frescos do banco.

---

## 1.5. Resumo Visual: `request` vs `session` vs `g`

| Objeto | O que é? | Duração (Ciclo de Vida) | Onde fica armazenado? | Analogia |
| :--- | :--- | :--- | :--- | :--- |
| **`request`** | Os dados que o navegador enviou (URL, método POST, cabeçalhos). | **1 Request** (Só leitura) | Memória do Servidor | A **carta** que o cliente entregou no balcão. |
| **`session`** | A "memória" de longo prazo do usuário (ex: ID logado). | **Múltiplos Requests** (Dias/Meses) | Navegador do Cliente (Cookie Assinado) | O **crachá de identificação** do cliente. |
| **`g`** | O rascunho temporário para compartilhar dados entre funções *durante* o request atual. | **1 Request** (Leitura e Escrita) | Memória do Servidor (Isolado por Thread) | A **prancheta** interna que os funcionários passam de mão em mão durante o atendimento. |

1. O Navegador envia a carta (**`request`**) junto com o crachá (**`session`**).
2. O Segurança (`before_request`) lê o crachá, vai ao arquivo morto (SQLite), pega a ficha completa do cliente e a coloca na prancheta (**`g.user`**).
3. O Atendente (`view function`) lê a prancheta (**`g`**) para fazer o trabalho sem precisar ir ao arquivo morto de novo.
4. O cliente vai embora. A carta é jogada fora, a prancheta é apagada. O crachá volta com o cliente para casa.

</details>

Crie o arquivo `flaskr/db.py`:

```python
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
```

### O Schema SQL
Crie o arquivo `flaskr/schema.sql`:

```sql
-- flaskr/schema.sql
DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS post;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

CREATE TABLE post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    author_id INTEGER NOT NULL,
    created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    FOREIGN KEY (author_id) REFERENCES user (id)
);
```

---

## 2. Ajustando a Factory (`flaskr/__init__.py`)

Precisamos dizer à nossa *Application Factory* para carregar o módulo de banco de dados que acabamos de criar.

**No arquivo `flaskr/__init__.py`, adicione as linhas marcadas no final da função `create_app`:**

```python
def create_app():
    app = Flask(__name__, instance_relative_config=True)
    # ... (código de configuração existente) ...

    from . import auth
    app.register_blueprint(auth.bp)

    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='index')

    # --- ADICIONE ESTAS 2 LINHAS ---
    from . import db
    db.init_app(app)
    # -------------------------------

    return app
```

---

## 3. Autenticação Real (`flaskr/auth.py`)

Na Aula 3, simulamos o login com `if username == 'admin'`. Agora vamos usar o SQLite e a biblioteca `werkzeug.security` para fazer o **hash** da senha (nunca guardamos senhas em texto puro!).

**Substitua o conteúdo do seu `flaskr/auth.py` por este:**

```python
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
    """Roda ANTES de qualquer view. Carrega o usuário do banco na variável g."""
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
```

**Crie os templates que faltam:**
*   `flaskr/templates/auth/register.html` (Apenas um formulário com `username` e `password` estendendo o `base.html`).
*   Ajuste o `login.html` para exibir as *flash messages* de erro/sucesso.

---

## 4. O CRUD do Blog (`flaskr/blog.py`)

Agora o coração da aplicação. Substitua a simulação de posts em memória por queries SQL reais. Note o uso do decorador `@login_required` que criamos acima e o uso de `JOIN` para cruzar o post com o nome do autor.

**Substitua o conteúdo do seu `flaskr/blog.py`:**

```python
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
```

**Crie os novos templates do blog:**
*   `flaskr/templates/blog/create.html` (Formulário com `title` e `body`).
*   `flaskr/templates/blog/update.html` (Formulário idêntico ao create, mas com `value="{{ post['title'] }}"` e textarea preenchido).
*   Ajuste `flaskr/templates/blog/index.html` para iterar sobre os posts reais, exibir o autor, a data e colocar botões de "Editar" (se `post['author_id'] == session.get('user_id')`) e um formulário com botão "Deletar".

---

## 5. Executando e Testando

Agora a mágica acontece. Abra o terminal na raiz do projeto (onde está a pasta `flaskr/`) e execute:

```bash
# 1. Inicializa o banco de dados (cria o arquivo instance/flaskr.sqlite)
flask --app flaskr init-db

# 2. Roda o servidor
flask --app flaskr run --debug
```

**Checklist de validação final:**
- [ ] O comando `init-db` criou o arquivo `instance/flaskr.sqlite`.
- [ ] Acessar `/auth/register` permite criar um usuário real no banco.
- [ ] O login funciona e o nome do usuário aparece na barra de navegação (via `g.user`).
- [ ] Usuários logados podem criar posts.
- [ ] Apenas o autor do post vê o botão de "Editar" e consegue acessar a rota `/update`.
- [ ] Tentar acessar `/create` sem estar logado redireciona para o login com flash de erro.
