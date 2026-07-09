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