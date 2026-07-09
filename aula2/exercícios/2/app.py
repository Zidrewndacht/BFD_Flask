from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "super-secreta-chave-de-desenvolvimento-123"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contato", methods=["GET", "POST"])
#...

if __name__ == "__main__":
    app.run(debug=True)