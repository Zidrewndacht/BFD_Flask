from flask import Flask
from datetime import datetime
import platform

app = Flask(__name__)


@app.route("/api/status")
def status():
    return {
        "servidor": "ok",
        "timestamp": datetime.now().isoformat(),
        "python": platform.python_version(),
        "sistema": platform.system()
    }

# Banco de dados simulado em memória, apenas para demonstração mínima:
USUARIOS = {
    1: {"nome": "Ana", "email": "ana@exemplo.com"},
    2: {"nome": "Bruno", "email": "bruno@exemplo.com"},
}

@app.route("/api/usuario/<int:id>")
def buscar_usuario(id):
    usuario = USUARIOS.get(id)
    if usuario is None:
        return {"erro": f"usuário {id} não encontrado"}, 404
    return usuario

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return {
        "erro": "página não encontrada",
        "rota_solicitada": str(e)
    }, 404

if __name__ == "__main__":
    app.run(debug=True)