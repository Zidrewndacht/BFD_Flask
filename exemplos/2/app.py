from flask import Flask
from datetime import datetime

app = Flask(__name__)

nome = "Luis"

@app.route("/")
def ola():
    agora = datetime.now().strftime("%H:%M:%S")
    return f"<h2>Olá, {nome}.</h2><p>Hora do servidor: {agora}</p>"

if __name__ == "__main__":
    app.run(debug=True)