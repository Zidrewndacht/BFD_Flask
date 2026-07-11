from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = "chave-secreta-para-o-quiz"

PERGUNTAS = [
    {
        "texto": "Qual é a capital da Austrália?",
        "opcoes": ["Sydney", "Melbourne", "Canberra", "Perth"],
        "resposta": "Canberra"
    },
    {
        "texto": "Qual linguagem o Flask usa?",
        "opcoes": ["Java", "Python", "Ruby", "PHP"],
        "resposta": "Python"
    },
    {
        "texto": "Qual o resultado de 1 + 1?",
        "opcoes": ["2", "10", "11", "3", "Depende"],
        "resposta": "Depende",
    },
]

@app.route("/")
def index():
    # Zera o estado do quiz ao voltar para o início
    session.clear()
    return render_template("quiz_index.html")

@app.route("/pergunta/<int:num>", methods=["GET", "POST"])
def pergunta(num):
    # Validação de ordem e existência da pergunta
    passo_atual = session.get("passo_atual", 1)
    if num != passo_atual or num < 1 or num > len(PERGUNTAS):
        return redirect(url_for('index'))
    
    # O índice da lista é num - 1
    p = PERGUNTAS[num - 1]
    
    if request.method == "POST":
        resposta_usuario = request.form.get("resposta")
        
        if resposta_usuario == p["resposta"]:
            session["acertos"] = session.get("acertos", 0) + 1
            flash("Resposta correta!", "success")
        else:
            flash(f"Errado! A resposta era: {p['resposta']}", "error")
        
        # Avança o passo
        session["passo_atual"] = num + 1
        
        # Redireciona para a próxima ou para o resultado
        if num == len(PERGUNTAS):
            return redirect(url_for('resultado'))
        else:
            return redirect(url_for('pergunta', num=num + 1))
    
    # GET: exibe a pergunta
    return render_template("quiz_pergunta.html", pergunta=p, num=num, total=len(PERGUNTAS))

@app.route("/resultado")
def resultado():
    acertos = session.get("acertos", 0)
    total = len(PERGUNTAS)
    session.clear() # Limpa a sessão ao finalizar
    return render_template("quiz_resultado.html", acertos=acertos, total=total)

if __name__ == "__main__":
    app.run(debug=True)