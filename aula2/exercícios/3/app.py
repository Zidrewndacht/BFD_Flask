from flask import #...

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

#...

if __name__ == "__main__":
    app.run(debug=True)