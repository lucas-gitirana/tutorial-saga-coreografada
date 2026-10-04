"""Serviço pagamentos (porta 8033): participante da saga.

Rotas:
  GET  /carteiras                          -> saldos e pagamentos
  POST /carteiras/<cliente>/deposito  {"valor"} -> adiciona saldo (administração)
  GET  /saude
"""
from flask import jsonify, request

from pagamentos import ESTADO_INICIAL, TRATADORES
from participante import Participante

servico = Participante("pagamentos", ESTADO_INICIAL, TRATADORES)
app = servico.app


@app.get("/carteiras")
def ver_carteiras():
    return jsonify(servico.estado)


@app.post("/carteiras/<cliente>/deposito")
def depositar(cliente: str):
    valor = (request.get_json(silent=True) or {}).get("valor", 0)
    if not isinstance(valor, (int, float)) or valor <= 0:
        return jsonify(erro="Informe um 'valor' maior que zero."), 400
    with servico.trava:
        saldos = servico.estado["saldos"]
        saldos[cliente] = round(saldos.get(cliente, 0.0) + valor, 2)
        servico.salvar()
    return jsonify(cliente=cliente, saldo=saldos[cliente])


if __name__ == "__main__":
    servico.iniciar()
