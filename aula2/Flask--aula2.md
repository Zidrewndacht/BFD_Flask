# Aula 2 — Dados do usuário, redirecionamentos e sessões

Na aula anterior, o fluxo de dados foi predominantemente **do servidor para o cliente**: o servidor recebia uma URL, buscava dados (ou usava valores fixos) e devolvia HTML ou JSON.

Agora, vamos tratar do sentido oposto: **dados vindos do navegador para o servidor**. Isso acontece quando um usuário preenche um formulário, faz login ou adiciona um produto ao carrinho, etc.

Três conceitos fundamentais:
1. O objeto **`request`** (a requisição que acabou de chegar).
2. **Redirecionamentos** e o padrão de segurança de formulários.
3. **Sessões** (como o servidor "lembra" de um usuário entre várias requisições).

---

## 1. O objeto `request`

Toda vez que o navegador faz uma requisição, ele envia um pacote de informações: URL, método HTTP, cabeçalhos, cookies e, frequentemente, dados de formulários.

O Flask empacota todas essas informações em um objeto chamado `request`:

```python
from flask import request
```

Esse objeto é uma *"context local"* — você pode usá-lo em qualquer *view function* e ele sempre conterá os dados da requisição **atual** que está sendo processada, mesmo com vários usuários simultâneos.

### 1.1 O método HTTP: `request.method`

O método HTTP indica a *intenção* da requisição. Os dois mais comuns em formulários web são:

| Método | Propósito | Onde os dados viajam |
|---|---|---|
| `GET` | **Receber** dados (ex: buscar um produto, exibir uma página). | Na própria URL, após o `?` (chamado de *query string*). |
| `POST` | **Enviar/Criar** dados (ex: criar uma conta, postar um comentário). | No **corpo** da requisição HTTP (invisível na URL). |

Você pode verificar o método usado na requisição atual através de `request.method`:

```python
@app.route("/contato", methods=["GET", "POST"])
def contato():
    if request.method == "POST":
        # O usuário enviou o formulário
        return "Formulário recebido!"
    # O usuário apenas abriu a página (GET)
    return "Preencha o formulário..."
```

Note o argumento `methods=["GET", "POST"]` no decorador `@app.route`. Por padrão, rotas do Flask aceitam apenas `GET`. Se você tentar enviar um `POST` para uma rota que não o permita, o Flask retornará erro **405 Method Not Allowed**.

### 1.2 Dados vindos na URL: `request.args`

É possível enviar formulário via `GET`. Neste caso, o navegador coloca os dados na URL.
Exemplo: `/buscar?q=flask&categoria=tutorial`

Para ler esses dados, usamos `request.args`, que funciona exatamente como um dicionário Python:

```python
@app.route("/buscar")
def buscar():
    termo = request.args.get("q", "")  # Pega o valor de 'q', ou "" se não existir
    return f"Você buscou por: {termo}"
```

> **Dica:** use sempre o método `.get("key", "default")` em vez de `request.args["key"]`. Se o usuário acessar `/buscar` sem o parâmetro `?q=...`, o acesso via colchetes levantaria um `KeyError` (resultando em erro 400 no navegador), enquanto `.get()` retorna o valor padrão de forma segura.

### 1.3 Dados vindos no corpo: `request.form`

Quando o método é `POST`, os dados do formulário viajam no corpo da requisição. Para acessá-los, usamos `request.form`, que também se comporta como um dicionário:

```python
@app.route("/login", methods=["POST"])
def login():
    usuario = request.form.get("username")
    senha = request.form.get("password")
    return f"Tentativa de login: {usuario}"
```

📚 Ref.: [Quickstart — The Request Object](https://flask.palletsprojects.com/en/stable/quickstart/#the-request-object)

---

## 2. Formulários em HTML:

O Flask não inventa nada sobre formulários HTML; ele apenas lê o que o navegador envia:

```html
<!-- templates/contato.html -->
<form method="POST" action="/contato">
    <label for="nome">Nome:</label>
    <input type="text" id="nome" name="nome" required>

    <label for="email">E-mail:</label>
    <input type="email" id="email" name="email" required>

    <label for="mensagem">Mensagem:</label>
    <textarea id="mensagem" name="mensagem"></textarea>

    <button type="submit">Enviar</button>
</form>
```

**Atributos críticos:**
- `method="POST"`: define o método HTTP. Se omitido, o padrão do HTML é `GET`.
- `action="/contato"`: define para qual URL os dados serão enviados. (Dica: em breve usaremos `url_for` aqui também).
- `name="..."` nos inputs: **este é o nome que o Flask usará como chave no dicionário `request.form`**. Sem o atributo `name`, o dado do input não é enviado ao servidor.

---

## 🔨 Exemplo guiado 1 — Saudação personalizada (20 min)

**Cenário:** o usuário informa seu nome e ano de nascimento. O servidor calcula a idade e devolve uma saudação personalizada. Se o ano for inválido, o formulário é reexibido com mensagem de erro.

```
saudacao/
├── app.py
└── templates/
    ├── base.html
    ├── index.html
    └── resultado.html
```

`templates/base.html`

```html
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>{% block titulo %}Saudação{% endblock %}</title>
</head>
<body>
    <main>
        {% block conteudo %}{% endblock %}
    </main>
</body>
</html>
```

`templates/index.html`

```html
{% extends "base.html" %}

{% block conteudo %}

    {% if erro %}
        <p style="color: red;"><strong>{{ erro }}</strong></p>
    {% endif %}

    <form method="POST" action="{{ url_for('index') }}">
        <p>
            <label>Nome: <input type="text" name="nome" value="{{ nome or '' }}"></label>
        </p>
        <p>
            <label>Ano de nascimento: <input type="text" name="ano" value="{{ ano or '' }}"></label>
        </p>
        <button type="submit">Calcular</button>
    </form>
{% endblock %}
```

Note o `value="{{ nome or '' }}"`: ele repopula o campo quando o formulário é reexibido após erro, evitando que o usuário digite tudo de novo.

`templates/resultado.html`

```html
{% extends "base.html" %}

{% block conteudo %}
    <h1>Olá, {{ nome }}!</h1>
    <p>Você tem aproximadamente <strong>{{ idade }}</strong> anos.</p>
    <p><a href="{{ url_for('index') }}">Voltar</a></p>
{% endblock %}
```

`app.py`

```python
from flask import Flask, render_template, request
from datetime import datetime

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    erro = None
    nome = ""
    ano = ""

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        ano = request.form.get("ano", "").strip()

        # Validação
        if not nome:
            erro = "Por favor, informe seu nome."
        elif not ano.isdigit():
            erro = "O ano de nascimento deve ser um número."
        else:
            ano_num = int(ano)
            ano_atual = datetime.now().year
            if ano_num < 1900 or ano_num > ano_atual:
                erro = f"Ano deve estar entre 1900 e {ano_atual}."
            else:
                # Dados válidos: calcula e exibe o resultado
                idade = ano_atual - ano_num
                return render_template("resultado.html", nome=nome, idade=idade)

    # GET ou POST com erro: reexibe o formulário
    return render_template("index.html", erro=erro, nome=nome, ano=ano)

if __name__ == "__main__":
    app.run(debug=True)
```

### O que observar ao rodar

1. Acesse `http://127.0.0.1:5000/`. O formulário aparece vazio.
2. Envie em branco → aparece a mensagem "Por favor, informe seu nome." e os campos mantêm o que foi digitado.
3. Digite "abc" no ano → mensagem de erro apropriada.
4. Digite nome e ano válidos → é renderizado `resultado.html` com a saudação.
5. **Teste crítico:** na página de resultado, aperte **F5**. O navegador exibe um alerta do tipo *"Confirmar reenvio de formulário"*. Se confirmar, o POST é reenviado e o resultado é recalculado. Isso é um **problema de usabilidade e integridade** — que vamos resolver na próxima seção.

---



### 🧪 Prática 1a — Formulário de Contato

Crie uma aplicação que exiba um formulário de contato e processe os dados enviados.

**Requisitos:**
1. Uma única rota `/contato` que aceita `GET` e `POST`.
2. No `GET`: renderiza o template `contato.html` com o formulário.
3. No `POST`: lê os campos `nome`, `email` e `mensagem` do `request.form`.
4. Validação manual simples: se o `nome` ou a `mensagem` estiverem vazios, renderize o próprio formulário novamente, passando uma variável `erro` com a mensagem "Nome e mensagem são obrigatórios.".
5. Se os dados forem válidos, retorne uma string HTML simples (sem template mesmo, por enquanto): `<h1>Obrigado, {nome}!</h1><p>Sua mensagem foi recebida.</p>`.

**Ponto de partida (`app.py`):**

```python
from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/contato", methods=["GET", "POST"])
def contato():
    # SUA LÓGICA AQUI
    pass

if __name__ == "__main__":
    app.run(debug=True)
```

**Checklist de validação:**
- [ ] Acessar `/contato` via navegador exibe o formulário.
- [ ] Enviar o formulário em branco exibe a mensagem de erro no próprio formulário.
- [ ] Preencher corretamente e enviar exibe a página de "Obrigado".
- [ ] **O teste do F5:** Após ver a página de "Obrigado", aperte **F5** no navegador. Observe o que o navegador pergunta e o que acontece se você confirmar.

---


## 🧪 Prática 1b — Formulário de conversão de temperatura

Construa uma aplicação similar ao exemplo guiado, mas com outro domínio.

**Cenário:** um formulário recebe uma temperatura em Celsius e a unidade de destino (Fahrenheit ou Kelvin). Ao submeter, o servidor converte e exibe o resultado. Valide:
- O valor deve ser numérico (aceita negativos).
- A unidade deve ser "F" ou "K".

**Fórmulas:**
- F = C × 9/5 + 32
- K = C + 273.15

**Requisitos:**
1. Uma única rota `/` que trata GET e POST.
2. Três templates: `base.html`, `index.html`, `resultado.html`.
3. Em caso de erro, o formulário é reexibido com a mensagem e os campos repopulados.
4. Em caso de sucesso, exibe uma página com a conversão.

---

## 3. Redirecionamentos e o padrão PRG (15 min)

### 3.1 O problema do F5

No exemplo guiado 1, você observou que responder a um `POST` com HTML direto causa um problema: ao atualizar a página (F5), o navegador reenvia o formulário. Em um sistema de pagamentos, isso poderia cobrar o cliente duas vezes; em um fórum, postaria o mesmo comentário duas vezes, etc..

### 3.2 Solução: POST/Redirect/GET (PRG)

1. O navegador faz o **POST** com os dados.
2. O servidor processa e, em vez de retornar HTML, responde com um **Redirecionamento** (HTTP 302) para uma URL de sucesso.
3. O navegador recebe o redirecionamento e faz um **GET** para a nova URL.
4. Se o usuário apertar F5 agora, ele apenas repetirá o GET — inofensivo.

### 3.3 `redirect` e `url_for`

O Flask fornece a função `redirect()` para gerar essa resposta de redirecionamento, e já a combinamos com `url_for()` (que você viu na Aula 1) para não *hardcodar* URLs:

```python
from flask import Flask, redirect, url_for, request

app = Flask(__name__)

@app.route("/sucesso")
def sucesso():
    return "<h1>Operação concluída com sucesso!</h1>"

@app.route("/acao", methods=["POST"])
def acao():
    # ... processa os dados do formulário ...
    
    # Redireciona o navegador para a rota 'sucesso'
    return redirect(url_for('sucesso'))
```

Quando o Flask executa `return redirect(...)`, ele não renderiza um template. Ele devolve ao navegador um cabeçalho HTTP especial (`Location: /sucesso`) com o status **302 Found**, instruindo o navegador a fazer uma nova requisição para aquele endereço.

📚 Ref.: [Quickstart — Redirects and Errors](https://flask.palletsprojects.com/en/stable/quickstart/#redirects-and-errors)

---

## 4. Flash Messages: Feedback entre requisições

### 4.1 O novo problema

Com o padrão PRG, resolvemos o problema do F5, mas criamos outro: como exibir uma mensagem de sucesso (ex: *"Contato enviado com sucesso!"*) ou de erro (ex: *"E-mail inválido!"*) na página para a qual redirecionamos o usuário?

Lembre-se: HTTP é **stateless** (sem estado). A requisição POST morre assim que o servidor responde com o redirecionamento. A próxima requisição (o GET da página de sucesso) é totalmente independente e "não sabe" o que aconteceu antes.

### 4.2 A solução: `flash()`

O Flask resolve isso com o sistema de **Flash Messages**. A função `flash()` armazena uma mensagem que será recuperada na **próxima** requisição do mesmo usuário, e apenas nela.

```python
from flask import flash, redirect, url_for

@app.route("/contato", methods=["POST"])
def contato():
    # ... validação ...
    flash("Sua mensagem foi enviada com sucesso!", "success")
    return redirect(url_for('index'))
```

### 4.3 O pré-requisito: `secret_key`

Para que o sistema de flash (e o sistema de sessões, que veremos a seguir) funcione, o Flask precisa assinar criptograficamente os dados que envia para o navegador via cookies. Para isso, você **deve** configurar uma chave secreta na sua aplicação:

```python
app.secret_key = "uma-string-secreta-qualquer-aqui"
# Em produção, isso viria de uma variável de ambiente, nunca hardcodado!
```

### 4.4 Recuperando as mensagens: `get_flashed_messages()`

As mensagens ficam disponíveis para o template através da função `get_flashed_messages()`, que o Jinja2 já conhece automaticamente. O ideal é colocar isso no seu `base.html`, para que as mensagens apareçam em qualquer página do site:

```html
<!-- dentro do <body> do base.html -->
{% with messages = get_flashed_messages(with_categories=true) %}
    {% if messages %}
        <ul class="flashes">
        {% for category, message in messages %}
            <li class="flash-{{ category }}">{{ message }}</li>
        {% endfor %}
        </ul>
    {% endif %}
{% endwith %}
```

O parâmetro `with_categories=true` permite que você passe um segundo argumento para o `flash()` (ex: `"success"`, `"error"`, `"warning"`) e use isso para estilizar a mensagem com CSS (ex: verde para sucesso, vermelho para erro).

📚 Ref.: [Quickstart — Message Flashing](https://flask.palletsprojects.com/en/stable/quickstart/#message-flashing)

---

## 🔨 Exemplo guiado 2 — Refatorando a saudação com PRG + Flash

Vamos pegar o exemplo guiado 1 e refatorá-lo para usar PRG e flash. Observe o **antes/depois** do problema do F5.

 `templates/base.html` (com bloco de flashes)

```html
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>{% block titulo %}Saudação{% endblock %}</title>
    <style>
        .flash-success { color: darkgreen; background: #efe; padding: 10px; border: 1px solid green; }
        .flash-error   { color: darkred;   background: #fee; padding: 10px; border: 1px solid red; }
    </style>
</head>
<body>
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
            {% for category, message in messages %}
                <div class="flash-{{ category }}">{{ message }}</div>
            {% endfor %}
        {% endif %}
    {% endwith %}

    <main>
        {% block conteudo %}{% endblock %}
    </main>
</body>
</html>
```

`app.py` refatorado

```python
from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = "chave-de-desenvolvimento-nao-use-em-producao"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        ano  = request.form.get("ano", "").strip()

        # Validação
        if not nome:
            flash("Por favor, informe seu nome.", "error")
            return redirect(url_for('index'))

        if not ano.isdigit():
            flash("O ano de nascimento deve ser um número.", "error")
            return redirect(url_for('index'))

        ano_num = int(ano)
        ano_atual = datetime.now().year
        if ano_num < 1900 or ano_num > ano_atual:
            flash(f"Ano deve estar entre 1900 e {ano_atual}.", "error")
            return redirect(url_for('index'))

        # Dados válidos: guarda na sessão e redireciona
        idade = ano_atual - ano_num
        session["nome"] = nome
        session["idade"] = idade
        flash(f"Saudação calculada para {nome}!", "success")
        return redirect(url_for('resultado'))

    return render_template("index.html")


@app.route("/resultado")
def resultado():
    nome = session.get("nome")
    idade = session.get("idade")
    if nome is None or idade is None:
        return redirect(url_for('index'))
    return render_template("resultado.html", nome=nome, idade=idade)


if __name__ == "__main__":
    app.run(debug=True)
```

`templates/index.html` (simplificado)

```html
{% extends "base.html" %}
{% block conteudo %}
    <h1>Descubra sua idade</h1>
    <form method="POST" action="{{ url_for('index') }}">
        <p><label>Nome: <input type="text" name="nome"></label></p>
        <p><label>Ano de nascimento: <input type="text" name="ano"></label></p>
        <button type="submit">Calcular</button>
    </form>
{% endblock %}
```

### O que observar ao rodar

1. Submeta com dados inválidos → é redirecionado para `/` com a mensagem de erro em vermelho no topo.
2. Aperte **F5** na página com erro → o navegador **não** pede confirmação. O GET é inofensivo.
3. Submeta com dados válidos → é redirecionado para `/resultado` com a mensagem verde "Saudação calculada!".
4. Aperte F5 em `/resultado` → apenas recarrega o GET. Sem alerta, sem reenvio.
5. Acesse `/resultado` diretamente sem ter feito o POST → é redirecionado para `/` (proteção via sessão).

*(Nota: para simplificar, ao redirecionar de volta para o formulário com erro, os campos virão em branco. Preencher automaticamente os campos após um redirect exige Sessão, que veremos a seguir).*

---

### 🧪 Prática 2 — Refatorando o Contato com PRG e Flash

Pegue o código da **Prática 1a** e refatore-o para usar o padrão PRG e Flash Messages.

**Requisitos:**
1. Crie uma rota `/` (`index`) que apenas renderiza um template `index.html` com uma mensagem de boas-vindas.
2. Adicione o bloco de exibição de flashes ao seu HTML.
3. Configure a `secret_key` no app.
4. No `/contato`:
   - Se os dados forem inválidos, use `flash("Erro: ...", "error")` e redirecione de volta para `/contato` (o GET exibirá o formulário novamente, agora com a mensagem de erro no topo).
   - Se os dados forem válidos, use `flash("Mensagem enviada!", "success")` e redirecione para `/`.

---

## 5. Sessões: Lembrando do usuário

### 5.1 O problema do HTTP Stateless

O protocolo HTTP não tem memória. Para o servidor, cada requisição é um evento isolado. Se o usuário faz login na página 1, ao clicar em um link para a página 2, o servidor não sabe que é a mesma pessoa.

Sistemas de e-commerce (carrinho de compras), redes sociais (usuário logado) e fóruns precisam "lembrar" do visitante entre as telas.

### 5.2 O objeto `session`

O Flask resolve isso com o objeto `session`. Ele funciona exatamente como um dicionário Python, mas o conteúdo dele é **persistido entre requisições** através de um *cookie* que o navegador armazena.

```python
from flask import session

@app.route("/login", methods=["POST"])
def login():
    # ... validar usuario e senha ...
    session["usuario_id"] = 42
    session["nome"] = "Ana"
    return redirect(url_for('perfil'))

@app.route("/perfil")
def perfil():
    if "usuario_id" not in session:
        return redirect(url_for('login'))
    
    return f"Olá, {session['nome']}!"

@app.route("/logout")
def logout():
    session.clear()  # ou session.pop("usuario_id", None)
    return redirect(url_for('index'))
```

### 5.3 Como funciona por baixo dos panos

Diferente de outras frameworks que guardam a sessão no servidor (em banco de dados ou memória), a sessão padrão do Flask é **client-side**:
1. Você grava `session["usuario"] = "Ana"`.
2. O Flask pega esse dicionário, serializa em texto, **assina criptograficamente** usando a `secret_key` e o envia para o navegador como um cookie chamado `session`.
3. Na próxima requisição, o navegador devolve o cookie.
4. O Flask verifica a assinatura (garantindo que o usuário não alterou o conteúdo) e disponibiliza os dados novamente no objeto `session`.

**Implicações importantes:**
- **O usuário NÃO pode alterar** os dados da sessão (a assinatura invalidaria o cookie).
- **O usuário PODE ler** os dados da sessão (o cookie é codificado em Base64, não criptografado). Portanto: **nunca guarde senhas, tokens de API ou dados sensíveis na sessão**.
- **Existe um limite de tamanho:** cookies têm limite de ~4KB. Sessões devem guardar apenas identificadores (ex: `user_id`), não bases de dados inteiras.

📚 Ref.: [Quickstart — Sessions](https://flask.palletsprojects.com/en/stable/quickstart/#sessions)

---

## 🔨 Exemplo guiado 3 — Contador de visitas e lista de favoritos

Vamos construir duas pequenas features que demonstram o uso de sessão: um contador persistente entre requisições e uma lista que o usuário alimenta.

### `app.py`

```python
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "chave-de-desenvolvimento"


@app.route("/")
def index():
    # Incrementa contador de visitas
    session["visitas"] = session.get("visitas", 0) + 1
    favoritos = session.get("favoritos", [])
    return render_template("index.html", visitas=session["visitas"], favoritos=favoritos)


@app.route("/adicionar", methods=["POST"])
def adicionar():
    item = request.form.get("item", "").strip()
    if item:
        favoritos = session.get("favoritos", [])
        favoritos.append(item)
        session["favoritos"] = favoritos  # reatribuição necessária para persistir
    return redirect(url_for('index'))


@app.route("/limpar")
def limpar():
    session.pop("favoritos", None)
    return redirect(url_for('index'))


@app.route("/resetar_tudo")
def resetar_tudo():
    session.clear()
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(debug=True)
```

### `templates/index.html`

```html
<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Favoritos</title></head>
<body>
    <h1>Meus favoritos</h1>
    <p>Você visitou esta página <strong>{{ visitas }}</strong> vez(es).</p>

    <form method="POST" action="{{ url_for('adicionar') }}">
        <input type="text" name="item" placeholder="Adicionar favorito..." required>
        <button type="submit">Adicionar</button>
    </form>

    {% if favoritos %}
        <ul>
        {% for f in favoritos %}
            <li>{{ f }}</li>
        {% endfor %}
        </ul>
        <p><a href="{{ url_for('limpar') }}">Limpar favoritos</a></p>
    {% else %}
        <p>Nenhum favorito ainda.</p>
    {% endif %}

    <p><a href="{{ url_for('resetar_tudo') }}">Resetar tudo (visitas + favoritos)</a></p>
</body>
</html>
```

### O que observar ao rodar

1. Cada refresh de `/` incrementa o contador — o Flask "lembra" do visitante.
2. Adicionar vários itens à lista funciona mesmo entre requisições distintas.
3. "Limpar favoritos" remove apenas a chave `favoritos`, mantendo `visitas`.
4. "Resetar tudo" chama `session.clear()` e apaga tudo.
5. Abra uma **aba anônima** do navegador e acesse a mesma URL: o contador começa do zero. A sessão é **por navegador/perfil**, não por servidor.

---

## 🧪 Prática 3 — Mini-quiz com sessão (30 min)

Um quiz de 3 perguntas que usa a sessão para lembrar as respostas do usuário à medida que ele avança.

**Fluxo:**
1. `/` exibe um botão "Iniciar Quiz". Ao clicar, a sessão é zerada e o usuário é redirecionado para `/pergunta/1`.
2. `/pergunta/<int:num>` exibe a pergunta atual.
   - GET: renderiza o formulário com as opções.
   - POST: verifica a resposta, incrementa acertos se correta, avança o passo e redireciona para `/pergunta/num+1` ou `/resultado`.
   - Proteção: se o usuário tentar pular etapas (ex: acessar `/pergunta/2` sem ter respondido 1), redireciona para `/`.
3. `/resultado` exibe o total de acertos e limpa a sessão.

**Estrutura de dados (forneça no `app.py`):**

```python
PERGUNTAS = [
    {
        "texto": "Qual é a capital da Austrália?",
        "opcoes": ["Sydney", "Melbourne", "Canberra", "Perth"],
        "resposta": "Canberra",
    },
    {
        "texto": "Qual linguagem o Flask usa?",
        "opcoes": ["Java", "Python", "Ruby", "PHP"],
        "resposta": "Python",
    },
    {
        "texto": "Qual o resultado de 1 + 1?",
        "opcoes": ["2", "10", "11", "3", "Depende"],
        "resposta": "Depende",
    },
]
```

**Requisitos:**
1. Use a `session` para armazenar:
   - `passo_atual` (inteiro: 1, 2 ou 3)
   - `acertos` (inteiro: começa em 0)
2. Rota `/` (`index`): exibe o botão "Iniciar". Ao clicar (via link simples), zera a sessão e redireciona para `/pergunta/1`.
3. Rota `/pergunta/<int:num>`:
   - Se o usuário tentar acessar uma pergunta fora de ordem (ex: `/pergunta/2` sem ter respondido a 1), redirecione para `/`.
   - No `GET`: exibe o template com a pergunta e as opções (como *radio buttons*).
   - No `POST`: verifica se a resposta enviada bate com o gabarito. Se sim, incrementa `session['acertos']`. Avança o `session['passo_atual']` e redireciona para a próxima pergunta (ou para `/resultado` se for a última).
4. Rota `/resultado`: exibe o total de acertos (ex: "Você acertou 2 de 3!") e limpa a sessão (`session.clear()`).

**Dicas:**
- Para validar a ordem, verifique se `session.get('passo_atual')` corresponde ao `<num>` da URL.
- Lembre-se de configurar a `secret_key`.
- Use flashes para dar feedback imediato após cada resposta ("Correto!" / "Errado!").

---

## 6. Recapitulação

| Conceito | Onde no Flask / HTML |
|---|---|
| Ler método da requisição | `request.method` |
| Ler parâmetros da URL (`?x=y`) | `request.args.get("x")` |
| Ler dados de formulário POST | `request.form.get("campo")` |
| Redirecionar o navegador | `return redirect(url_for('rota'))` |
| Enviar feedback entre telas | `flash("mensagem", "categoria")` |
| Exibir feedback no template | `get_flashed_messages(with_categories=true)` |
| Guardar dados entre requisições | `session["chave"] = valor` |
| Limpar dados do usuário | `session.clear()` ou `session.pop("chave")` |

### O ciclo completo Request-Response-Session

1. O navegador envia uma requisição (GET ou POST) com dados.
2. O Flask popula o objeto `request` com esses dados.
3. A *view function* processa (valida, calcula, consulta BD etc.).
4. Opcionalmente grava algo na `session` (que vira cookie assinado).
5. Opcionalmente registra um `flash` (também usa a sessão).
6. Retorna HTML, JSON ou `redirect()`.
7. O Flask monta a resposta, injeta o cookie de sessão e envia ao navegador.

### Referências

1. Flask — Quickstart (Request, Sessions, Flashing, Redirects): https://flask.palletsprojects.com/en/stable/quickstart/
2. Werkzeug — Secure Cookie / Session implementation: https://werkzeug.palletsprojects.com/en/stable/secure-cookie/