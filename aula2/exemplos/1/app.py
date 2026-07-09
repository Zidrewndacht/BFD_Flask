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