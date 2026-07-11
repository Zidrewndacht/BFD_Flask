from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "super-secreta-chave-de-desenvolvimento-123"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/contato", methods=["GET", "POST"])
def contato():
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        mensagem = request.form.get("mensagem", "").strip()
        
        if not nome or not mensagem:
            flash("Nome e mensagem são obrigatórios.", "error")
            return redirect(url_for('contato'))
        
        # Dados válidos
        flash(f"Obrigado, {nome}! Sua mensagem foi recebida e não faremos nada com ela.", "success")
        return redirect(url_for('index'))
    
    # GET: exibe o formulário
    return render_template("contato.html")

if __name__ == "__main__":
    app.run(debug=True)