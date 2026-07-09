from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/contato", methods=["GET", "POST"])
def contato():
    # SUA LÓGICA AQUI
    

if __name__ == "__main__":
    app.run(debug=True)