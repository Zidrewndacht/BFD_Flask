# Aula 3 — Estrutura de Projeto, Application Factory e Blueprints

Nas aulas 1 e 2, construímos aplicações Flask em um único arquivo `app.py`. Essa abordagem é excelente para protótipos, APIs mínimas e exercícios focados em um único conceito. 

No entanto, à medida que um projeto real cresce — adicionamos autenticação, CRUD de entidades, upload de arquivos, configurações de banco de dados e dezenas de rotas — o `app.py` se torna um monolito ilegível. Pior ainda: ele se torna **impossível de testar** e **difícil de manter** por múltiplas pessoas.

Nesta aula, vamos abandonar o arquivo único e adotar o padrão de organização de projetos Flask recomendado pelo [tutorial oficial](https://flask.palletsprojects.com/en/stable/tutorial/): o **Application Factory Pattern** combinado com **Blueprints**.

---

## 1. O problema do `app.py` monolítico

Considere o que acontece quando seu projeto atinge 1000 linhas de código com rotas de autenticação, blog, painel administrativo e configuração de banco de dados, tudo no mesmo arquivo:

```python
# app.py (O monolito)
from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "chave-hardcoded"
DATABASE = "banco.db"

# ... 50 linhas de funções auxiliares de banco de dados ...
# ... 100 linhas de rotas de autenticação ...
# ... 100 linhas de rotas do blog ...
# ... 100 linhas de rotas administrativas ...

if __name__ == "__main__":
    app.run(debug=True)
```

Essa estrutura gera quatro problemas graves de engenharia de software:

| Problema | Impacto no projeto |
|---|---|
| **Acoplamento** | Lógica de negócio, configuração de infraestrutura (BD) e interface web (rotas/templates) estão misturadas. Mudar o banco de dados exige editar o mesmo arquivo que contém o HTML. |
| **Imports circulares** | Se você tentar mover a lógica de BD para um arquivo `db.py` e importar `app` lá (para acessar `app.config`), e o `app.py` importar `db.py` para registrar rotas, o Python entra em colapso por dependência circular. |
| **Testabilidade nula** | Para testar uma rota, você precisa importar o `app` global. Mas esse `app` já está configurado com o banco de dados de desenvolvimento (`banco.db`). Como testar com um banco efêmero em memória (`:memory:`) sem reescrever o código? |
| **Instância única** | Ferramentas de CLI, tarefas em background ou testes de carga podem precisar de múltiplas instâncias do app com configurações diferentes. Um objeto `app` global no nível do módulo impede isso. |

A solução para todos esses problemas é tratar a aplicação Flask não como um *objeto global*, mas como o **resultado de uma função**.

---

## 2. Application Factory Pattern

O **Application Factory Pattern** (Padrão de Fábrica de Aplicações) encapsula a criação e configuração da instância do Flask dentro de uma função, convencionalmente chamada `create_app()`.

### 2.1 A estrutura básica

Em vez de instanciar `Flask` no nível global, fazemos isso dentro da função:

```python
# flaskr/__init__.py
import os
from flask import Flask

def create_app(test_config=None):
    # Cria a instância do Flask
    app = Flask(__name__, instance_relative_config=True)
    
    # Configurações padrão
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )

    # Sobrescreve com configurações de teste, se fornecidas
    if test_config is None:
        app.config.from_pyfile('config.py', silent=True)
    else:
        app.config.from_mapping(test_config)

    # Garante que a pasta instance exista
    os.makedirs(app.instance_path, exist_ok=True)

    # Rota de teste
    @app.route('/hello')
    def hello():
        return 'Hello, World!'

    return app
```

### 2.2 O que mudou?

1. **`Flask(__name__, instance_relative_config=True)`:**
   - `__name__` agora não é mais `'__main__'` (o script executado). Como este código está dentro de um pacote chamado `flaskr`, `__name__` será `'flaskr'`. Isso diz ao Flask para procurar as pastas `templates/` e `static/` **dentro** do pacote `flaskr/`.
   - `instance_relative_config=True` instrui o Flask a procurar arquivos de configuração (e o banco de dados) em uma pasta especial chamada `instance/`, que fica **fora** do pacote versionado.

2. **A pasta `instance/`:**
   - É uma pasta criada automaticamente na raiz do projeto, paralela ao pacote `flaskr/`.
   - Serve para armazenar dados que **não devem ir para o Git**: o arquivo do banco de dados SQLite (`flaskr.sqlite`), chaves secretas de produção, tokens de API, etc.
   - O caminho absoluto para ela é acessível via `app.instance_path`.

3. **Múltiplas instâncias:**
   - Agora podemos chamar `create_app()` quantas vezes quisermos.
   - O servidor de desenvolvimento chama uma vez.
   - O framework de testes (`pytest`) chama uma vez para cada teste, passando um `test_config` com um banco de dados provisório em memória.
   - Scripts de manutenção podem chamar uma vez com configurações de leitura-apenas.

### 2.3 A CLI do Flask

Com a factory, não usamos mais `python app.py`. Usamos a **CLI oficial do Flask**, que descobre a factory automaticamente se você apontar para o pacote:

```bash
# No terminal, na raiz do projeto (fora da pasta flaskr/)
flask --app flaskr run --debug
```

O Flask importa o pacote `flaskr`, procura a função `create_app()`, a executa e inicia o servidor com a instância retornada. O `--debug` ativa o modo de desenvolvimento (recarregamento automático e Werkzeug Debugger).

📚 **Ref.:** [Tutorial — Application Setup](https://flask.palletsprojects.com/en/stable/tutorial/factory/)

---

## 3. 🧪 Prática 5 — Refatorando para Factory Pattern

Vamos pegar o **Exemplo Guiado 3 da Aula 2** (Contador de visitas e lista de favoritos) e transformá-lo em um projeto estruturado com Application Factory.

### 3.1 Estrutura de pastas alvo

Crie a seguinte estrutura no seu projeto:

```
projeto_favoritos/
├── flaskr/
│   ├── __init__.py       # A factory viverá aqui
│   └── templates/
│       └── index.html    # O template da Aula 2
├── .venv/
└── requirements.txt
```

### 3.2 O código da factory

Copie o código abaixo para `flaskr/__init__.py`:

```python
# flaskr/__init__.py
import os
from flask import Flask, render_template, request, redirect, url_for, session

def create_app():
    app = Flask(__name__)
    
    # Configuração mínima para a sessão funcionar
    app.secret_key = "chave-de-desenvolvimento"
    
    # As rotas agora são registradas DENTRO da factory
    @app.route("/")
    def index():
        session["visitas"] = session.get("visitas", 0) + 1
        favoritos = session.get("favoritos", [])
        return render_template("index.html", visitas=session["visitas"], favoritos=favoritos)

    @app.route("/adicionar", methods=["POST"])
    def adicionar():
        item = request.form.get("item", "").strip()
        if item:
            favoritos = session.get("favoritos", [])
            favoritos.append(item)
            session["favoritos"] = favoritos
        return redirect(url_for('index'))

    @app.route("/limpar")
    def limpar():
        session.pop("favoritos", None)
        return redirect(url_for('index'))

    return app
```

Mova o `index.html` da Aula 2 para `flaskr/templates/index.html` (o conteúdo HTML permanece idêntico).

### 3.3 Executando

No terminal, na raiz do projeto (onde está a pasta `flaskr/`), execute:

```bash
flask --app flaskr run --debug
```

Acesse `http://127.0.0.1:5000/`. O comportamento deve ser idêntico ao da Aula 2, mas agora o código está encapsulado em um pacote Python reutilizável.

**Pergunta para refletir:** O que aconteceria se você tentasse importar `create_app` em um script de teste (`test_app.py`) e chamá-la duas vezes com configurações diferentes? 
*Resposta:* Você teria duas instâncias independentes do Flask, cada uma com seu próprio estado e configuração — algo impossível com o `app.py` global.

---

## 4. Blueprints: Modularizando rotas

Mesmo com a factory, se colocarmos todas as rotas dentro de `__init__.py`, o arquivo voltará a crescer rapidamente. Um blog real tem rotas de autenticação (login, registro, logout), rotas de posts (criar, editar, deletar), rotas administrativas, etc.

**Blueprints** são a solução do Flask para organizar rotas em múltiplos arquivos. Um Blueprint é como uma "mini-aplicação" que você desenha separadamente e depois "encaixa" na aplicação principal.

### 4.1 Criando um Blueprint

Um Blueprint é criado em seu próprio arquivo de módulo (ex: `auth.py`):

```python
# flaskr/auth.py
from flask import Blueprint

# Cria o blueprint
bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login')
def login():
    return 'Página de Login'

@bp.route('/register')
def register():
    return 'Página de Registro'
```

Parâmetros importantes:
- `'auth'`: O **nome** do blueprint. Será usado como prefixo no `url_for()`.
- `__name__`: O nome do módulo atual (`'flaskr.auth'`). O Flask usa isso para localizar recursos.
- `url_prefix='/auth'`: Todas as rotas deste blueprint terão `/auth` prep automaticamente. `/login` vira `/auth/login`.

### 4.2 Registrando o Blueprint na Factory

O Blueprint não faz nada até ser registrado na aplicação. Isso é feito dentro da `create_app()`:

```python
# flaskr/__init__.py
from flask import Flask

def create_app():
    app = Flask(__name__)
    app.secret_key = "dev"

    # Importa o módulo do blueprint
    from . import auth
    
    # Registra o blueprint na aplicação
    app.register_blueprint(auth.bp)

    return app
```

O `from . import auth` é um **import relativo**: importa o arquivo `auth.py` que está no mesmo pacote (`flaskr/`).

### 4.3 A mudança crucial no `url_for()`

Quando você registra um Blueprint, o Flask altera o **namespace** dos endpoints. O nome da view function agora é prefixado com o nome do blueprint, separado por ponto.

| Antes (sem blueprint) | Depois (com blueprint `auth`) |
|---|---|
| `url_for('login')` | `url_for('auth.login')` |
| `url_for('register')` | `url_for('auth.register')` |

Isso é fundamental para evitar colisões de nomes. Se você tiver um blueprint `auth` e um blueprint `admin`, ambos podem ter uma rota chamada `index` sem conflito: `url_for('auth.index')` e `url_for('admin.index')`.

📚 **Ref.:** [Tutorial — Blueprints and Views](https://flask.palletsprojects.com/en/stable/tutorial/views/)

---

## 5. Organização de pastas: O padrão Flaskr

A documentação oficial do Flask usa um projeto de blog chamado **Flaskr** como exemplo canônico. A estrutura de pastas abaixo é o padrão da indústria para aplicações Flask de médio e grande porte:

```
flask-tutorial/              ← Raiz do projeto (onde você roda 'flask run')
├── flaskr/                  ← O pacote Python principal
│   ├── __init__.py          ← Application Factory (create_app)
│   ├── auth.py              ← Blueprint de autenticação
│   ├── blog.py              ← Blueprint do blog
│   ├── db.py                ← Lógica de conexão com o BD (Aula 4)
│   ├── templates/           ← Templates HTML (Jinja2)
│   │   ├── base.html        ← Layout compartilhado
│   │   ├── auth/            ← Templates específicos do blueprint auth
│   │   │   ├── login.html
│   │   │   └── register.html
│   │   └── blog/            ← Templates específicos do blueprint blog
│   │       ├── index.html
│   │       └── create.html
│   └── static/              ← CSS, JS, imagens
│       └── style.css
├── instance/                ← Criada automaticamente, NÃO vai pro Git
│   └── flaskr.sqlite        ← Banco de dados local
├── tests/                   ← Testes automatizados (futuro)
├── .venv/                   ← Ambiente virtual
├── .gitignore               ← Deve ignorar instance/, .venv/, __pycache__/
└── requirements.txt         ← Dependências do projeto
```

### 5.1 Por que essa estrutura funciona?

1. **Separação de responsabilidades:** Cada blueprint cuida de um domínio de negócio (autenticação, blog, admin).
2. **Templates organizados:** A subpasta `templates/auth/` espelha o nome do blueprint. Quando você chama `render_template('auth/login.html')`, o Flask sabe exatamente onde procurar.
3. **Pacote instalável:** Como `flaskr/` é um pacote Python com `__init__.py`, no futuro você poderá empacotá-lo com `pip install -e .` e instalá-lo em qualquer servidor.
4. **Segurança:** A pasta `instance/` fica fora do pacote, facilitando a exclusão via `.gitignore` para que senhas e bancos de dados locais nunca vazem para o repositório.

---

## 6. 🧪 Prática 6 — Criando os blueprints `auth` e `blog`

Vamos construir a estrutura canônica do Flaskr, criando dois blueprints funcionais que navegam entre si.

### 6.1 Passo 1: Limpar e estruturar

Apague o conteúdo atual de `flaskr/__init__.py` e crie a estrutura de pastas:

```
projeto_flaskr/
├── flaskr/
│   ├── __init__.py
│   ├── auth.py
│   ├── blog.py
│   └── templates/
│       ├── base.html
│       ├── auth/
│       │   └── login.html
│       └── blog/
│           └── index.html
└── .venv/
```

### 6.2 Passo 2: O template base (`flaskr/templates/base.html`)

Este template define o layout compartilhado e a navegação entre os blueprints.

```html
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>{% block title %}Flaskr{% endblock %}</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        nav { background: #333; padding: 10px; margin-bottom: 20px; }
        nav a { color: white; margin-right: 15px; text-decoration: none; }
        nav a:hover { text-decoration: underline; }
        .flash { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .flash-error { background: #fee; color: #c00; border: 1px solid #c00; }
        .flash-success { background: #efe; color: #060; border: 1px solid #060; }
    </style>
</head>
<body>
    <nav>
        <a href="{{ url_for('blog.index') }}">Flaskr</a>
        <a href="{{ url_for('auth.login') }}">Log In</a>
    </nav>

    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash flash-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <section>
        {% block content %}{% endblock %}
    </section>
</body>
</html>
```

Note o uso de `url_for('blog.index')` e `url_for('auth.login')`. Esses endpoints ainda não existem, mas já estamos escrevendo os links de forma resiliente.

### 6.3 Passo 3: O Blueprint `auth` (`flaskr/auth.py`)

```python
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
```

### 6.4 Passo 4: O template de login (`flaskr/templates/auth/login.html`)

```html
{% extends 'base.html' %}

{% block title %}Log In — Flaskr{% endblock %}

{% block content %}
    <h1>Log In</h1>
    <form method="POST">
        <label>Username: <input type="text" name="username" required></label><br><br>
        <label>Password: <input type="password" name="password" required></label><br><br>
        <button type="submit">Entrar</button>
    </form>
    <p><small>Dica de teste: admin / 123</small></p>
{% endblock %}
```

### 6.5 Passo 5: O Blueprint `blog` (`flaskr/blog.py`)

```python
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
        
    return "<h1>Formulário de criação de post (Aula 4)</h1>"
```

*Nota:* Adicione `from flask import request` no topo do `blog.py`.

### 6.6 Passo 6: O template do blog (`flaskr/templates/blog/index.html`)

```html
{% extends 'base.html' %}

{% block title %}Flaskr — Blog{% endblock %}

{% block content %}
    <h1>Posts</h1>
    
    {% if 'user_id' in session %}
        <p>Olá, {{ session['username'] }}! <a href="{{ url_for('auth.logout') }}">Sair</a> | <a href="{{ url_for('blog.create') }}">Novo Post</a></p>
    {% endif %}

    {% for post in posts %}
        <article>
            <h2>{{ post.title }}</h2>
            <p>{{ post.body }}</p>
        </article>
        <hr>
    {% else %}
        <p>Nenhum post ainda.</p>
    {% endfor %}
{% endblock %}
```

### 6.7 Passo 7: A Factory (`flaskr/__init__.py`)

Finalmente, a fábrica que une tudo:

```python
# flaskr/__init__.py
import os
from flask import Flask

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
    )
    
    os.makedirs(app.instance_path, exist_ok=True)

    # Registra o blueprint auth
    from . import auth
    app.register_blueprint(auth.bp)

    # Registra o blueprint blog
    from . import blog
    app.register_blueprint(blog.bp)

    # Define a rota raiz '/' como um alias para blog.index
    # Isso permite que http://127.0.0.1:5000/ funcione
    app.add_url_rule('/', endpoint='index')

    return app
```

### 6.8 Executando e testando

```bash
flask --app flaskr run --debug
```

**Checklist de validação:**
- [ ] ACESSAR `/` redireciona ou exibe a lista de posts do blog.
- [ ] Clicar em "Log In" leva a `/auth/login`.
- [ ] Submeter o formulário com `admin`/`123` redireciona para `/` com flash de sucesso e exibe "Olá, admin!".
- [ ] Estando logado, clicar em "Novo Post" leva a `/create`.
- [ ] Clicar em "Sair" limpa a sessão e remove as opções de criação.
- [ ] Tentar acessar `/create` sem estar logado redireciona para o login com flash de erro.

---

## 7. Configuração externa e a pasta `instance/` (160–180')

Em produção, você **nunca** deve manter `SECRET_KEY = 'dev'` ou o caminho do banco de dados hardcoded no código-fonte. O Flask resolve isso com um sistema de configuração em camadas.

### 7.1 O objeto `app.config`

`app.config` é um dicionário Python que armazena todas as configurações da aplicação. O Flask e suas extensões leem esse dicionário para ajustar seu comportamento.

### 7.2 Carregando configurações

A factory que construímos já usa dois métodos de carregamento:

```python
# 1. Valores padrão (sempre aplicados)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE=os.path.join(app.instance_path, 'flaskr.sqlite'),
)

# 2. Sobrescrita via arquivo Python (opcional)
app.config.from_pyfile('config.py', silent=True)
```

O método `from_pyfile('config.py', silent=True)` procura um arquivo chamado `config.py` **dentro da pasta `instance/`**. Se o arquivo existir, ele é executado e quaisquer variáveis definidas nele sobrescrevem as configurações padrão. O `silent=True` impede que o Flask quebre se o arquivo não existir (comum em desenvolvimento).

### 7.3 Exemplo de `instance/config.py` (Produção)

Em um servidor de produção, você criaria o arquivo `instance/config.py` (que **não** é versionado no Git):

```python
# instance/config.py (NÃO PUBLICAR no Git!)
SECRET_KEY = 'uma-string-aleatoria-extremamente-longa-e-segura-aqui'
DATABASE = '/var/lib/flaskr/production.sqlite'
```

### 7.4 Variáveis de ambiente

Para configurações sensíveis como senhas de banco de dados ou chaves de API de terceiros, a prática moderna é usar variáveis de ambiente, lidas via `os.environ`:

```python
import os

# Em create_app():
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev')
```

Você pode definir a variável no terminal antes de rodar o app:
```bash
# Linux/Mac
export FLASK_SECRET_KEY="minha-chave-secreta"
flask --app flaskr run

# Windows (PowerShell)
$env:FLASK_SECRET_KEY="minha-chave-secreta"
flask --app flaskr run
```

### 7.5 Gerando uma SECRET_KEY segura

A `SECRET_KEY` é usada para assinar criptograficamente os cookies de sessão e as flash messages. Se um atacante descobri-la, ele poderá forjar sessões e se passar por qualquer usuário.

Gere uma chave forte com o módulo `secrets` do Python:

```bash
python -c 'import secrets; print(secrets.token_hex())'
```

Copie a string hexadecimal gerada e cole no seu `instance/config.py` ou na variável de ambiente.

📚 **Ref.:** [Tutorial — Configuration Basics](https://flask.palletsprojects.com/en/stable/config/)

---

## Resumo da Aula 3

| Conceito | Para que serve |
|---|---|
| **Application Factory (`create_app`)** | Cria instâncias independentes do Flask, permitindo testes, múltiplos ambientes e evitando imports circulares. |
| **Pasta `instance/`** | Armazena dados sensíveis e locais (banco SQLite, `config.py`) que não devem ser versionados no Git. |
| **Blueprints** | Modularizam rotas em arquivos separados, organizando o projeto por domínio de negócio (auth, blog, admin). |
| **`url_prefix`** | Adiciona um prefixo automático a todas as rotas de um blueprint (ex: `/auth/login`). |
| **`url_for('bp.endpoint')`** | Gera URLs de forma resiliente, usando o namespace do blueprint para evitar colisões de nomes. |
| **`app.config.from_pyfile`** | Carrega configurações externas de um arquivo Python, permitindo sobrescrever valores padrão em produção. |
