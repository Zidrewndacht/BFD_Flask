# calc_service.py
# Módulo com lógica pura: não importa flask, não lê input(), apenas calcula.

def calcular_imc(peso: float, altura: float) -> dict:
    if altura <= 0 or peso <= 0:
        raise ValueError("peso e altura devem ser positivos")
    imc = peso / (altura ** 2)
    if imc < 18.5:
        categoria = "Abaixo do peso"
    elif imc < 25:
        categoria = "Peso normal"
    elif imc < 30:
        categoria = "Sobrepeso"
    else:
        categoria = "Obesidade"
    return {"imc": round(imc, 2), "categoria": categoria}


def calcular_eficiencia(distancia: float, litros: float, preco: float) -> dict:
    if litros <= 0 or distancia <= 0 or preco <= 0:
        raise ValueError("todos os valores devem ser positivos")
    eficiencia = distancia / litros
    custo_total = litros * preco
    custo_km = custo_total / distancia
    return {
        "eficiencia_km_l": round(eficiencia, 2),
        "custo_total": round(custo_total, 2),
        "custo_por_km": round(custo_km, 4),
    }