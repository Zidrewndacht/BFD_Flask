from flask import Flask, render_template

app = Flask(__name__)

@app.route("/ola/<nome>")
def ola(nome):
    return render_template("ola.html", pessoa=nome)

# falta algo aqui.