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