# Flask

Flask é um **microframework WSGI** para construir aplicações web em Python. "Micro" não significa limitado: significa que o núcleo é pequeno e extensões são adicionadas conforme a necessidade.

<details>
<summary><strong>Detalhes sobre WSGI</strong></summary>

**WSGI** (Web Server Gateway Interface, definido na [PEP 3333](https://peps.python.org/pep-3333/)) é um padrão Python que define como um servidor web (como Nginx, Apache, Gunicorn) se comunica com uma aplicação Python. O servidor recebe a requisição HTTP, traduz para o formato WSGI, chama a aplicação, e devolve a resposta ao cliente.

Flask é uma aplicação WSGI. Durante o desenvolvimento, ele inclui um servidor embutido para que você não precise configurar um servidor externo. Em produção, você usaria um servidor WSGI dedicado (Gunicorn, Waitress), mas isso fica para disciplinas futuras.
</details>

Na prática, Flask faz três coisas:

1. **Roteia** requisições HTTP para funções Python (chamadas *view functions*).
2. **Constrói** uma resposta (`Response`) a partir do retorno da função.
3. **Renderiza** templates HTML com dados dinâmicos via Jinja2.

Tudo o mais (banco de dados, autenticação, formulários, APIs REST) é extensão. Nesta aula tratamos apenas do núcleo.

### 1.1 Criando o ambiente

Abra o terminal na pasta do projeto e crie um ambiente virtual:

```bash
# Lembre-se de usar um ambiente virtual:
python -m venv .venv
.venv\Scripts\activate
# instale Flask
pip install flask
# atualize requirements.txt após instalar tudo que decidir usar
pip freeze > requirements.txt
```

### 1.2 O menor aplicativo possível

Crie um arquivo chamado `app.py`:

```python
from flask import Flask

app = Flask(__name__)

@app.route("/")
def ola():
    return "<h1>Olá, mundo!</h1>"

if __name__ == "__main__":
    app.run(debug=True)
```

Execute com:

```bash
python app.py
```

Abra `http://127.0.0.1:5000` no navegador. Você verá o texto renderizado como HTML.

**Pontos importantes do código acima:**

- `Flask(__name__)` cria a aplicação. `__name__` informa ao Flask onde procurar templates e arquivos estáticos (no mesmo diretório do módulo atual).
- `@app.route("/")` é um **decorador** que associa a URL `/` à função abaixo dele.
- `app.run(debug=True)` inicia o servidor de desenvolvimento embutido do Flask. O modo `debug` recarrega automaticamente o servidor quando você salva um `.py` e mostra erros detalhados no navegador quando ocorrerem.
- Lembrete: o `if __name__ == "__main__"` garante que o servidor só inicie quando você executa o arquivo diretamente com `python app.py`. Se o arquivo for importado como módulo em outro código, o servidor não inicia automaticamente.

> **Nota de segurança:** `debug=True` nunca deve ser usado em produção. Ele expõe um depurador interativo (Werkzeug Debugger) que permite executar código Python arbitrário no servidor via navegador.

<details>
<summary><strong>Detalhes sobre Werkzeug Debugger</strong></summary>

Quando você roda um app Flask com `debug=True`, o framework embute uma ferramenta chamada **Werkzeug Debugger**. Ela intercepta qualquer exceção não tratada que ocorra durante uma requisição e, em vez de devolver uma página de erro 500 genérica, renderiza uma **tela interativa no navegador** com:

- O *traceback* completo (a pilha de chamadas de funções que levou ao erro)
- O valor de cada variável local em cada nível da pilha
- O código-fonte ao redor da linha que falhou
- Um **console Python embutido** em cada frame da pilha, que permite executar código arbitrário no processo do servidor

Tudo isso rodando dentro do navegador, em tempo real, enquanto o servidor está ativo.

## 2. Como ele aparece na prática

Considere este código intencionalmente quebrado:

```python
from flask import Flask

app = Flask(__name__)

USUARIOS = {
    1: {"nome": "Ana", "saldo": 1500},
    2: {"nome": "Bruno", "saldo": 300},
}

@app.route("/usuario/<int:id>")
def ver_usuario(id):
    usuario = USUARIOS[id]  # falha se id não existir
    return usuario

if __name__ == "__main__":
    app.run(debug=True)
```

Ao acessar `http://127.0.0.1:5000/usuario/99`, você verá no navegador:

```
KeyError
KeyError: 99

Traceback (most recent call last)
  File "app.py", line 11, in ver_usuario
    usuario = USUARIOS[id]
                ↑
  • id = 99
  • USUARIOS = {1: {'nome': 'Ana', 'saldo': 1500}, 2: {'nome': 'Bruno', 'saldo': 300}}
  • usuario = undefined
```

Cada linha do traceback é clicável e revela o código-fonte e as variáveis locais daquele frame. Isso é extremamente útil em desenvolvimento: você identifica o bug em segundos, sem precisar inserir `print()` ao longo do código.

## 3. O console interativo

No rodapé da tela de erro, há um botão **"Console"** (ou, em versões mais recentes do Werkzeug, um ícone de terminal em cada frame da pilha). Ao clicar, abre-se um prompt Python **que roda dentro do processo do servidor Flask**, com acesso ao mesmo contexto da view function que falhou.

No exemplo acima, você poderia digitar no console:

```python
>>> USUARIOS.keys()
dict_keys([1, 2])

>>> import os
>>> os.listdir('.')
['app.py', 'templates', 'static', '.venv', 'requirements.txt']

>>> os.environ.get('PATH')
'/usr/bin:/bin:...'
```

Em desenvolvimento, isso é fantástico: você inspeciona o estado do servidor sem reiniciá-lo. Em produção, é uma **backdoor completa**.

## 4. Por que é catastrófico em produção

Se um app Flask com `debug=True` for exposto à internet:

1. **Qualquer visitante** pode forçar uma exceção (passando um ID inexistente, uma string onde se espera número, etc.) e acessar o traceback.
2. O traceback já vaza informações sensíveis: nomes de arquivos, estrutura de pastas, valores de variáveis, chaves de configuração, queries SQL, trechos de código proprietário.
3. Se o atacante conseguir desbloquear o console interativo (veja item 5), ele ganha um **shell Python no servidor** com os mesmos privilégios do usuário que roda o processo Flask. Na prática:
   - Lê o conteúdo de qualquer arquivo que o processo pode ler (incluindo `.env`, credenciais de banco, chaves privadas)
   - Executa comandos do sistema operacional via `os.system()` ou `subprocess`
   - Modifica o código-fonte da aplicação em disco
   - Pivota para outras máquinas da rede interna
   - Instala malware persistente

Esse vetor de ataque é tão conhecido que bots varrem a internet procurando apps Flask/Django com debug ativo. Não é um risco teórico — é uma das primeiras coisas que um *pentester* verifica.

## 5. A proteção por PIN

Desde o Werkzeug 0.11 (2015), o console interativo exige um **PIN de 9 dígitos** para ser desbloqueado. Esse PIN é:

- Gerado deterministicamente a partir de características da máquina (MAC address, nome da máquina, caminho do módulo, etc.)
- Exibido **uma única vez** no terminal onde o servidor foi iniciado, na inicialização:

```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
 * WARNING: This is a development server. Do not use it in a production deployment.
 * Running on all addresses (0.0.0.0)
 * Debugger PIN: 123-456-789
```

Para desbloquear o console no navegador, o atacante precisaria ter acesso ao terminal onde o servidor está rodando — o que, em desenvolvimento local, é você mesmo. Essa camada adicional de proteção reduz, mas **não elimina**, o risco:

- O PIN pode ser capturado por loggers, shoulder surfing, ou gravação de tela
- O traceback em si (sem o console) já é informação sensível demais para expor publicamente
- A existência do depurador indica ao atacante que o app está mal configurado, o que sugere outras vulnerabilidades prováveis

## 6. Como usar com segurança

### Regra absoluta
`debug=True` **nunca** em produção. Ponto.

### Em desenvolvimento
É não apenas aceitável quanto **recomendado** usar `debug=True` (ou `flask run --debug`). O ganho de produtividade é enorme. Apenas garanta que:

1. O servidor rode apenas em `127.0.0.1` (padrão do Flask), nunca em `0.0.0.0`, para evitar que outras máquinas da rede local acessem o depurador.
2. Você nunca exponha a porta 5000 via túnel (ngrok, Cloudflare Tunnel) com debug ativo.
3. O PIN do debugger seja tratado como credencial sensível.

### Em produção
A variável de ambiente `FLASK_DEBUG=0` (ou a ausência dela) e o uso de um servidor WSGI dedicado (como Gunicorn) garantem que o depurador nem seja carregado. Exemplo de comando de produção:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app   # apenas disponível para Linux
```

O Gunicorn ignora `app.run()` e, portanto, o depurador do Werkzeug nem entra em jogo.

## 7. Demonstração:

Para consolidar o conceito com os alunos, vale uma demonstração ao vivo de 5 minutos:

1. Rode o app do item 2 com `debug=True` em `127.0.0.1:5000`.
2. Acesse `/usuario/99` e mostre o traceback colorido.
3. Clique em "Console", digite `import os; os.listdir('.')` e mostre os arquivos do projeto listados no navegador.
4. Pergunte à turma: *"Se essa máquina estivesse na internet, o que um atacante poderia fazer?"*
5. Mostre onde o PIN aparece no terminal e explique a proteção.
6. Finalize desligando o servidor e rodando novamente com `FLASK_DEBUG=0` — o mesmo `/usuario/99` agora retorna uma página 500 genérica do Werkzeug, sem traceback nem console.

## 8. Referência oficial

- Werkzeug Debugger: https://werkzeug.palletsprojects.com/en/stable/debug/
- Flask — Debug Mode: https://flask.palletsprojects.com/en/stable/quickstart/#debug-mode
- CVE-2024-34069 (vulnerabilidade no debugger do Werkzeug que permitia bypass do PIN em certas configurações — reforça que mesmo a proteção por PIN não é infalível): https://github.com/pallets/werkzeug/security/advisories/GHSA-2g68-c3qc-8985
</details>

---

📚 Ref.: [Quickstart — A Minimal Application](https://flask.palletsprojects.com/en/stable/quickstart/#a-minimal-application)


### 🧪 Prática rápida 1

Altere `ola()` para retornar:
1. Seu nome, a partir de uma variável, como `<h2>`
2. A hora atual do servidor (use `from datetime import datetime`)


---

## 2. Rotas e variáveis de URL

Rotas no Flask suportam partes variáveis, escritas entre `< >` na string de rota. O valor capturado é passado como argumento para a view function com o mesmo nome.

```python
@app.route("/usuario/<nome>")
def saudacao(nome):
    return f"Olá, {nome}!"
```

A URL `/usuario/ana` chama `saudacao("ana")`.

### 2.1 Conversores de tipo

Por padrão, variáveis de rota são strings. Use conversores para validar e converter o valor antes da chamada:

| Conversor | Aceita |
|---|---|
| `string` (padrão) | qualquer texto sem `/` |
| `int` | inteiros positivos |
| `float` | números com ponto decimal |
| `path` | texto incluindo `/` |
| `uuid` | UUIDs válidos |

```python
@app.route("/imc/<float:peso>/<float:altura>")
def calc_imc(peso, altura):
    imc = peso / (altura ** 2)
    return f"IMC: {imc:.2f}"
```

A URL `/imc/70/1.75` passa `peso=70.0` e `altura=1.75` como **float**, não como string. Se o usuário enviar `/imc/abc/1.75`, o Flask retorna **404** — o conversor rejeita o valor antes mesmo da função ser chamada.

### 2.2 Múltiplas rotas para a mesma função

Um mesmo handler pode responder a várias URLs:

```python
@app.route("/")
@app.route("/inicio")
def home():
    return "Página inicial"
```

📚 Ref.: [Quickstart — Routing](https://flask.palletsprojects.com/en/stable/quickstart/#routing)

---

## 3. Retornando dados estruturados

Uma view function pode retornar três coisas básicas:

| Retorno | Resultado |
|---|---|
| `str` | HTML/texto, status 200 |
| `dict` / `list` | JSON automático (status 200) |
| Tupla `(body, status)` | conteúdo + código HTTP |
| Objeto `Response` | controle total (cabeçalhos, cookies) |

### 3.1 JSON automático

Retornar um dicionário converte o resultado para `application/json`. O exemplo abaixo usa `datetime` para gerar um timestamp diferente a cada requisição — isso permite verificar visualmente, ao recarregar a página, que o Flask executa a view function **a cada request**, não apenas uma vez:

```python
from datetime import datetime
import platform

@app.route("/api/status")
def status():
    return {
        "servidor": "ok",
        "timestamp": datetime.now().isoformat(),
        "python": platform.python_version(),
        "sistema": platform.system()
    }
```

Ao acessar `/api/status` repetidamente no navegador, o campo `timestamp` muda a cada recarga, enquanto `python` e `sistema` permanecem constantes (dependem apenas do ambiente onde o servidor está rodando). Essa distinção é útil para começar a diferenciar **dados dinâmicos** (gerados por request) de **dados de ambiente** (fixos durante a vida do processo).

📚 Ref.: [Quickstart — About Responses](https://flask.palletsprojects.com/en/stable/quickstart/#about-responses)

### 3.2 Status HTTP personalizado

Retorne uma tupla para alterar o código. Isso é útil quando **a rota existe, mas o recurso específico solicitado não**:

```python
# Banco de dados simulado em memória, apenas para demonstração mínima:
USUARIOS = {
    1: {"nome": "Ana", "email": "ana@exemplo.com"},
    2: {"nome": "Bruno", "email": "bruno@exemplo.com"},
}

@app.route("/api/usuario/<int:id>")
def buscar_usuario(id):
    usuario = USUARIOS.get(id)
    if usuario is None:
        return {"erro": f"usuário {id} não encontrado"}, 404
    return usuario
```

Teste:
- `http://127.0.0.1:5000/api/usuario/1` → retorna os dados de Ana (status 200)
- `http://127.0.0.1:5000/api/usuario/99` → retorna `{"erro": "usuário 99 não encontrado"}` com status **404**

A distinção é importante: a **rota** `/api/usuario/<int:id>` existe e foi encontrada pelo Flask. O que não existe é o **recurso** (o usuário 99 no banco de dados). Por isso a função é executada, decide que não há dados para retornar, e sinaliza isso com o código HTTP apropriado.

### 3.3 O verdadeiro 404: quando a rota não existe

O que acontece se você acessar `/pagina-que-nao-existe`? O Flask retorna uma página 404 padrão automaticamente — nenhuma view function é chamada, porque nenhuma rota corresponde à URL.

Você pode **personalizar** essa página padrão registrando um handler de erro:

```python
@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return {
        "erro": "página não encontrada",
        "rota_solicitada": str(e)
    }, 404
```

Agora qualquer URL inexistente retorna seu JSON personalizado em vez da página HTML padrão do Flask. Esse é o verdadeiro "fallback" para rotas inexistentes.

> **Analogia:** a diferença entre 3.2 e 3.3 é como a diferença entre "o prédio existe, mas o apartamento 99 não" (3.2) e "esse endereço nem existe na cidade" (3.3).

📚 Ref.:
- [Quickstart — About Responses](https://flask.palletsprojects.com/en/stable/quickstart/#about-responses)
- [Quickstart — Error handlers](https://flask.palletsprojects.com/en/stable/quickstart/#error-handlers)

### 🧪 Prática 2 — Reuso do código Python anterior

Você já escreveu `imc.py` e `gas_eff.py` na disciplina de Python. Agora vai transformá-los em endpoints HTTP, reaproveitando a lógica de negócio.

**Passos:**

1. Copie o código abaixo para um arquivo novo `calc_service.py` no mesmo diretório de `app.py`:

```python
# calc_service.py
# Módulo com lógica pura: não importa flask, não lê input(), apenas calcula.

def calcular_imc(peso: float, altura: float) -> dict:
    if altura <= 0 or peso <= 0:
        raise ValueError("peso e altura devem ser positivos")
    imc = peso / (altura ** 2)
    if imc < 18.5:
        categoria = "Abaixo do peso"
    elif imc < 25:
        categoria = "Peso normal"
    elif imc < 30:
        categoria = "Sobrepeso"
    else:
        categoria = "Obesidade"
    return {"imc": round(imc, 2), "categoria": categoria}


def calcular_eficiencia(distancia: float, litros: float, preco: float) -> dict:
    if litros <= 0 or distancia <= 0 or preco <= 0:
        raise ValueError("todos os valores devem ser positivos")
    eficiencia = distancia / litros
    custo_total = litros * preco
    custo_km = custo_total / distancia
    return {
        "eficiencia_km_l": round(eficiencia, 2),
        "custo_total": round(custo_total, 2),
        "custo_por_km": round(custo_km, 4),
    }
```

Observe: esse módulo não sabe que Flask existe. Ele recebe valores e devolve um `dict`. Essa separação entre **lógica** e **interface** (web, terminal, teste) é um princípio fundamental de design de software — e o `__name__ == "__main__"` que você estudou na aula anterior existe justamente para permitir esse reaproveitamento.

2. Em `app.py`, importe o módulo e crie os endpoints:

```python
from flask import Flask
import calc_service

app = Flask(__name__)


@app.route("/imc/<float:peso>/<float:altura>")
def rota_imc(peso, altura):
    try:
        resultado = calc_service.calcular_imc(peso, altura)
        return resultado
    except ValueError as e:
        return {"erro": str(e)}, 400


@app.route("/eficiencia/<float:distancia>/<float:litros>/<float:preco>")
def rota_eficiencia(distancia, litros, preco):
    try:
        resultado = calc_service.calcular_eficiencia(distancia, litros, preco)
        return resultado
    except ValueError as e:
        return {"erro": str(e)}, 400


@app.route("/")
def indice():
    return {
        "endpoints_disponiveis": [
            "/imc/<peso>/<altura>",
            "/eficiencia/<distancia>/<litros>/<preco>",
        ]
    }


@app.errorhandler(404)
def rota_inexistente(e):
    return {"erro": "endpoint não encontrado", "detalhe": str(e)}, 404


if __name__ == "__main__":
    app.run(debug=True)
```

3. Rode o servidor e teste no navegador ou em outra aba:
   - `http://127.0.0.1:5000/`
   - `http://127.0.0.1:5000/imc/70/1.75`
   - `http://127.0.0.1:5000/eficiencia/300/25/6.2`
   - `http://127.0.0.1:5000/imc/-5/1.7` → observe o código HTTP **400** no navegador (abra as ferramentas de desenvolvedor → aba *Network*)
   - `http://127.0.0.1:5000/qualquer-coisa` → observe o código HTTP **404** e seu JSON personalizado

**Pergunta para refletir:** o que aconteceria se você removesse o conversor `<float:>` da rota `/imc/<peso>/<altura>` e o usuário passasse `abc` no lugar do peso? Teste e observe o código HTTP retornado.

<details>
<summary><strong>Ver resposta da pergunta para refletir</strong></summary>

Sem o conversor `<float:>`, o Flask trata `peso` como string. A URL `/imc/abc/1.7` passa `"abc"` (string) para `rota_imc`. O `calc_service.calcular_imc` tentaria fazer `"abc" / (1.7 ** 2)` e levantaria um `TypeError` (não um `ValueError`). Como `except ValueError` não captura `TypeError`, o Flask retornaria um erro 500 (Internal Server Error) com a pilha de exceção visível (porque estamos em modo debug).

Isso ilustra por que os conversores de tipo são úteis: eles validam a entrada **antes** da função ser chamada, transformando entradas inválidas em 404 de forma limpa.

</details>

---

## 4. Templates Jinja2

Retornar HTML como string Python funciona para uma linha, mas rapidamente se torna ilegível. Flask resolve isso com **Jinja2**, um motor de templates que separa o HTML da lógica.

### 4.1 Estrutura de pastas

Flask adota uma **convenção padrão** de diretórios. Você pode alterar esses caminhos passando parâmetros ao construtor (`Flask(__name__, template_folder="views", static_folder="assets")`), mas seguir a convenção é fortemente recomendado: é o que a documentação, os tutoriais e toda a comunidade usam.

Na mesma pasta de `app.py`, crie:

```
projeto/
├── app.py
├── templates/          ← arquivos .html vão aqui
│   └── ola.html
└── calc_service.py
```

### 4.2 `render_template`

Substitua o retorno string por:

```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/ola/<nome>")
def ola(nome):
    return render_template("ola.html", pessoa=nome)
```

E no arquivo `templates/ola.html`:

```html
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>Saudação</title>
</head>
<body>
    <h1>Olá, {{ pessoa }}!</h1>
</body>
</html>
```

A função `render_template("ola.html", pessoa=nome)` faz duas coisas:
1. Carrega o arquivo `templates/ola.html`.
2. Passa `nome` para dentro do template sob o identificador `pessoa`.

### 4.3 Sintaxe do Jinja2

Há três tipos principais de marcação:

| Sintaxe | Função |
|---|---|
| `{{ expressão }}` | **Substituição:** avalia a expressão e insere o resultado |
| `{% comando %}` | **Controle:** `if`, `for`, `extends`, `block`, `macro` |
| `{# comentário #}` | Comentário — não aparece no HTML final |

Exemplos:

```html
{% if idade >= 18 %}
    <p>Maior de idade.</p>
{% else %}
    <p>Menor de idade.</p>
{% endif %}

<ul>
{% for item in lista %}
    <li>{{ item }}</li>
{% endfor %}
</ul>
```

> **Escape automático:** o Jinja2 **escapa** por padrão o conteúdo de `{{ variavel }}` para HTML, convertendo `<` em `&lt;` etc. Isso previne injeção de HTML/XSS. 

📚 Ref.:
- [Quickstart — Rendering Templates](https://flask.palletsprojects.com/en/stable/quickstart/#rendering-templates)
- [Jinja2 Template Designer's Documentation](https://jinja.palletsprojects.com/en/stable/templates/)

---

## 5. Herança de templates

Páginas de um mesmo site geralmente compartilham cabeçalho, rodapé e menu. Em vez de repetir o mesmo HTML em cada template, usamos **herança**: um template `base.html` define os blocos que os filhos preenchem.

### 5.1 `base.html`

```html
<!doctype html>
<html lang="pt-br">
<head>
    <meta charset="utf-8">
    <title>{% block titulo %}Meu site{% endblock %}</title>
</head>
<body>
    <nav>
        <a href="/">Início</a> |
        <a href="/sobre">Sobre</a> |
        <a href="/projetos">Projetos</a>
    </nav>

    <main>
        {% block conteudo %}{% endblock %}
    </main>

    <footer>
        <p>&copy; 2026</p>
    </footer>
</body>
</html>
```

`{% block nome %}{% endblock %}` declara uma **região sobrescrevível**.

### 5.2 `sobre.html` (filho)

```html
{% extends "base.html" %}

{% block titulo %}Sobre — Meu site{% endblock %}

{% block conteudo %}
    <h1>Sobre</h1>
    <p>Este é um site de exemplo construído com Flask e Jinja2.</p>
{% endblock %}
```

`{% extends "base.html" %}` deve ser a **primeira** diretiva do arquivo filho. Os blocos não preenchidos ficam com o conteúdo padrão definido em `base.html`.

📚 Ref.: [Jinja2 — Template Inheritance](https://jinja.palletsprojects.com/en/stable/templates/#template-inheritance)

---

## 6. Arquivos estáticos

CSS, JavaScript e imagens ficam na pasta `static/` — seguindo a mesma convenção padrão de `templates/`:

```
projeto/
├── app.py
├── templates/
│   ├── base.html
│   └── sobre.html
└── static/
    └── style.css
```

### 6.1 `url_for` e por que evitar caminhos *hardcoded*

Você poderia linkar o CSS assim:

```html
<!-- ❌ Funciona, mas é frágil -->
<link rel="stylesheet" href="/static/style.css">
```

O problema dessa abordagem é que ela **acopla o template a um caminho de arquivo específico**. Se no futuro você:

- mudar o nome da pasta estática (ex: de `static/` para `assets/`),
- servir a aplicação sob um prefixo (ex: `meusite.com/app/` em vez de `meusite.com/`),
- ou adicionar versionamento/cache busting (`style.css?v=2`),

...cada link *hardcoded* no seu HTML teria que ser atualizado manualmente.

`url_for` resolve isso porque ele constrói a URL a partir do **nome da função** (chamado de *endpoint* no Flask), não do caminho do arquivo:

```html
<!-- ✅ Resiliente a mudanças de estrutura -->
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
```

O que acontece por baixo dos panos:

1. Flask registra internamente um endpoint chamado `'static'` que sabe onde a pasta de arquivos estáticos está localizada.
2. `url_for('static', filename='style.css')` pergunta ao Flask: "qual é a URL para servir o arquivo `style.css` do endpoint `static`?"
3. O Flask consulta a configuração atual (`static_folder`, `static_url_path`) e devolve o caminho correto para aquele momento.

Para rotas de view functions, o princípio é o mesmo:

```html
<!-- ❌ Frágil: se você mudar @app.route("/sobre") para @app.route("/about"), o link quebra -->
<a href="/sobre">Sobre</a>

<!-- ✅ Resiliente: acompanha qualquer mudança na rota da função 'sobre' -->
<a href="{{ url_for('sobre') }}">Sobre</a>
```

> **Resumo da regra:** em templates, use `url_for` para qualquer URL interna (páginas, CSS, JS, imagens). Reserve caminhos hardcoded apenas para URLs externas (ex: `https://cdn.exemplo.com/lib.js`).

📚 Ref.: [Quickstart — Static Files](https://flask.palletsprojects.com/en/stable/quickstart/#static-files) e [Quickstart — URL Building](https://flask.palletsprojects.com/en/stable/quickstart/#url-building)

---

### 🧪 Prática 2 — Site pessoal de 3 páginas

Construa um pequeno site pessoal aplicando tudo que vimos: rotas, templates, herança e arquivos estáticos.

**Estrutura esperada:**

```
site_pessoal/
├── app.py
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── sobre.html
│   └── projetos.html
└── static/
    └── style.css
```

**Requisitos:**

1. `base.html` contém o cabeçalho de navegação (links para as 3 páginas), bloco de `titulo`, bloco de `conteudo` e um rodapé.
2. `style.css` aplica: fonte sans-serif, largura máxima de 700px no `<main>`, margem automática para centralizar, cor de fundo leve no `body`.
3. Cada página:
   - **Início** (`/`): um `<h1>` com seu nome e um parágrafo curto de apresentação.
   - **Sobre** (`/sobre`): uma lista `<ul>` com 3–5 habilidades suas, iterada no template via `{% for %}` a partir de uma **lista Python** passada pela view function.
   - **Projetos** (`/projetos`): uma lista de 3 projetos, onde cada projeto é um **dicionário** com chaves `nome`, `descricao` e `url`. Use `{% for %}` no template para iterar sobre `projetos` e `{{ p.nome }}`, `{{ p.descricao }}` etc.
4. Use `url_for('static', filename='style.css')` no `<head>` do base.
5. Os links de navegação devem usar `url_for('index')`, `url_for('sobre')`, `url_for('projetos')`.
6. Cada `<title>` deve sobrescrever o bloco `titulo` com o nome da página.

**Ponto de partida para `app.py`:**

```python
from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sobre")
def sobre():
    habilidades = [
        "Python",
        "HTML/CSS",
        "SQL",
        "Git",
    ]
    return render_template("sobre.html", habilidades=habilidades)


@app.route("/projetos")
def projetos():
    lista = [
        {
            "nome": "Calculadora de IMC",
            "descricao": "API Flask reutilizando código Python anterior.",
            "url": "#",
        },
        {
            "nome": "Site pessoal",
            "descricao": "Este mesmo site, construído como prática de Jinja2.",
            "url": "#",
        },
        {
            "nome": "Gerenciador de tarefas",
            "descricao": "CLI Python com persistência em SQLite.",
            "url": "#",
        },
    ]
    return render_template("projetos.html", projetos=lista)


if __name__ == "__main__":
    app.run(debug=True)
```

Você deve escrever apenas os arquivos `base.html`, `index.html`, `sobre.html`, `projetos.html` e `style.css`.

**Checklist de validação:**

- [ ] Navegar entre as 3 páginas funciona via links no cabeçalho.
- [ ] O `<title>` da aba do navegador muda em cada página.
- [ ] O rodapé aparece nas três páginas mesmo estando declarado uma única vez em `base.html`.
- [ ] O CSS é carregado (você vê o `body` com cor de fundo).
- [ ] Na página `/projetos`, os dados vêm de Python — alterar `lista` em `app.py` altera a página sem mexer no HTML.

---

## 7. Recapitulação

| Conceito | Onde no Flask |
|---|---|
| Aplicação | `Flask(__name__)` |
| Associar URL → função | `@app.route("/...")` |
| Parâmetros na URL | `<tipo:nome>` na string da rota |
| Servidor de dev | `flask run` / `app.run(debug=True)` |
| Retorno de view function | `str`, `dict`, `(body, status)`, `Response` |
| Rota existe, recurso não | `return corpo, 404` dentro da view function |
| Rota não existe (fallback) | `@app.errorhandler(404)` |
| HTML dinâmico | `render_template("arq.html", var=val)` |
| Sintaxe de template | `{{ }}` expressão · `{% %}` comando · `{# #}` comentário |
| Reuso de layout | `{% extends %}` + `{% block %}` |
| URLs internas resilientes | `url_for('nome_da_funcao')` e `url_for('static', filename='...')` |

### Convenção padrão de pastas do Flask

```
projeto/
├── app.py                 # ponto de entrada
├── templates/             # arquivos .html (Jinja2) — configurável via template_folder
│   ├── base.html
│   └── pagina.html
└── static/                # CSS, JS, imagens — configurável via static_folder
    ├── style.css
    └── logo.png
```

### Referências

1. Flask — Quickstart: https://flask.palletsprojects.com/en/stable/quickstart/
2. Flask — Tutorial oficial (será a base da Aula 3): https://flask.palletsprojects.com/en/stable/tutorial/
3. Jinja2 — Template Designer's Documentation: https://jinja.palletsprojects.com/en/stable/templates/
4. Werkzeug (biblioteca subjacente ao Flask): https://werkzeug.palletsprojects.com/