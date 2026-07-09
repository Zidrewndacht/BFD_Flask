from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    erro = None
    valor_str = ""
    unidade = "F"

    if request.method == "POST":
        valor_str = request.form.get("valor", "").strip()
        unidade = request.form.get("unidade", "F").strip().upper()

        try:
            celsius = float(valor_str)
        except ValueError:
            erro = "Informe um valor numérico (ex: 25 ou -3.5)."
        else:
            if unidade not in ("F", "K"):
                erro = "Unidade deve ser F (Fahrenheit) ou K (Kelvin)."
            else:
                if unidade == "F":
                    convertido = celsius * 9 / 5 + 32
                    nome_unidade = "Fahrenheit"
                else:
                    convertido = celsius + 273.15
                    nome_unidade = "Kelvin"

                return render_template(
                    "resultado.html",
                    celsius=celsius,
                    convertido=convertido,
                    unidade=nome_unidade,
                )

    return render_template("index.html", erro=erro, valor=valor_str, unidade=unidade)

if __name__ == "__main__":
    app.run(debug=True)