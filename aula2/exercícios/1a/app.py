from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/contato", methods=["GET", "POST"])
def contato():
    erro = None
    
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        mensagem = request.form.get("mensagem", "").strip()
        
        if not nome or not mensagem:
            erro = "Nome e mensagem são obrigatórios."
        else:
            # Dados válidos (em uma app real, salvaríamos no banco ou enviaríamos email)
            return f"<h1>Obrigado, {nome}!</h1><p>Sua mensagem foi recebida com sucesso e descartada com carinho.</p><a href='/contato'>Voltar</a>"
    
    # Se é GET, ou se houve erro no POST, renderiza o formulário
    return render_template("contato.html", erro=erro)

if __name__ == "__main__":
    app.run(debug=True)