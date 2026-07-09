from flask import Flask
import Flask.aula1.exercícios.prat2.calc_service as calc_service

app = Flask(__name__)


@app.route("/imc/<float:peso>/<float:altura>")
def rota_imc(peso, altura):
    try:
        resultado = calc_service.calcular_imc(peso, altura)
        return resultado
    except ValueError as e:
        return {"erro": str(e)}, 400


@app.route("/eficiencia/<float:distancia>/<float:litros>/<float:preco>")
def rota_eficiencia(distancia, litros, preco):
    try:
        resultado = calc_service.calcular_eficiencia(distancia, litros, preco)
        return resultado
    except ValueError as e:
        return {"erro": str(e)}, 400


@app.route("/")
def indice():
    return {
        "endpoints_disponiveis": [
            "/imc/<peso>/<altura>",
            "/eficiencia/<distancia>/<litros>/<preco>",
        ]
    }


@app.errorhandler(404)
def rota_inexistente(e):
    return {"erro": "endpoint não encontrado", "detalhe": str(e)}, 404


if __name__ == "__main__":
    app.run(debug=True)