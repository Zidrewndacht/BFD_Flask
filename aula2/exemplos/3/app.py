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