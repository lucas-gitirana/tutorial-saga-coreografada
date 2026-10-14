"""Serviço pedidos (porta 8031): inicia a saga e acompanha o desfecho.

Rotas:
  POST /pedidos  {"cliente", "produto", "quantidade"} -> cria pedido PENDENTE
  GET  /pedidos                    -> todos os pedidos
  GET  /pedidos/resumo             -> todos os pedidos, uma linha cada (texto)
  GET  /pedidos/<id>               -> um pedido
  GET  /pedidos/<id>/historico     -> linha do tempo da saga deste pedido (texto)
  GET  /saude
"""
from flask import jsonify, request

from participante import Participante
from pedidos import ESTADO_INICIAL, TRATADORES, ErroDePedido, criar_pedido

# guardar_historico: o pedidos também escuta a fila "saga.historico" (assina "#", todos os eventos)
servico = Participante("pedidos", ESTADO_INICIAL, TRATADORES, guardar_historico=True)
app = servico.app


@app.post("/pedidos")
def rota_criar_pedido():
    dados = request.get_json(silent=True) or {}
    try:
        with servico.trava:
            pedido, eventos = criar_pedido(servico.estado, str(dados.get("cliente") or "").strip(),
                                           dados.get("produto"), dados.get("quantidade", 1))
            servico.salvar()
    except ErroDePedido as erro:
        return jsonify(erro=str(erro)), 400
    print(f"[pedidos] pedido {pedido['pedido_id']} criado como PENDENTE")
    servico.publicar(eventos)
    # 202 Accepted: o pedido foi aceito, mas o desfecho depende da saga
    return jsonify(pedido), 202


@app.get("/pedidos")
def listar_pedidos():
    return jsonify(list(servico.estado["pedidos"].values()))


@app.get("/pedidos/resumo")
def resumo_dos_pedidos():
    linhas = [f"{p['pedido_id']:<16} {p['produto']} x{p['quantidade']:<4} {p['status']:<11} {p['motivo'] or ''}"
              for p in servico.estado["pedidos"].values()]
    return "\n".join(linhas or ["(nenhum pedido ainda)"]) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.get("/pedidos/<pedido_id>")
def obter_pedido(pedido_id: str):
    pedido = servico.estado["pedidos"].get(pedido_id)
    if pedido is None:
        return jsonify(erro=f"Pedido '{pedido_id}' não encontrado."), 404
    return jsonify(pedido)


@app.get("/pedidos/<pedido_id>/historico")
def historico(pedido_id: str):
    eventos = sorted(servico.historico(pedido_id), key=lambda e: e["publicado_em_ms"])
    if not eventos:
        return f"Nenhum evento para o pedido '{pedido_id}'.\n", 404, {"Content-Type": "text/plain; charset=utf-8"}
    inicio = eventos[0]["publicado_em_ms"]
    linhas = [f"+{(e['publicado_em_ms'] - inicio) / 1000:6.1f} s   {e['origem']:<10} publicou  {e['tipo']}" for e in eventos]
    return "\n".join(linhas) + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


if __name__ == "__main__":
    servico.iniciar()
