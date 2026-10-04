"""Serviço estoque (porta 8032): participante da saga.

Rotas:
  GET  /estoque                          -> quantidades disponíveis e reservas
  POST /estoque/<produto>/reposicao  {"quantidade"} -> repõe estoque (administração)
  GET  /saude
"""
from flask import jsonify, request

from estoque import ESTADO_INICIAL, TRATADORES
from participante import Participante

servico = Participante("estoque", ESTADO_INICIAL, TRATADORES)
app = servico.app


@app.get("/estoque")
def ver_estoque():
    return jsonify(servico.estado)


@app.post("/estoque/<produto>/reposicao")
def repor(produto: str):
    quantidade = (request.get_json(silent=True) or {}).get("quantidade", 0)
    if not isinstance(quantidade, int) or quantidade <= 0:
        return jsonify(erro="Informe uma 'quantidade' inteira maior que zero."), 400
    with servico.trava:
        disponivel = servico.estado["disponivel"]
        disponivel[produto] = disponivel.get(produto, 0) + quantidade
        servico.salvar()
    return jsonify(produto=produto, disponivel=disponivel[produto])


if __name__ == "__main__":
    servico.iniciar()
