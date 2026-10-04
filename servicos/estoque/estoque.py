"""Regras do serviço de ESTOQUE: reserva produtos e desfaz reservas.

  PedidoCriado      -> reserva o produto  -> EstoqueReservado | EstoqueIndisponivel
  PagamentoRecusado -> COMPENSAÇÃO: libera a reserva -> EstoqueLiberado

Funções puras: recebem o estado do serviço e os dados do evento e devolvem a
lista de eventos a publicar.
"""
from __future__ import annotations

ESTADO_INICIAL = {
    "disponivel": {"teclado": 10, "mouse": 20, "monitor": 2},
    "reservas": {},  # pedido_id -> {"produto", "quantidade", "status": RESERVADA | LIBERADA}
}


def evento(tipo: str, **dados) -> dict:
    return {"tipo": tipo, "dados": dados}


# ---------------------------------------------------------------------------
# Exemplo pronto: a transação local do estoque
# ---------------------------------------------------------------------------
def ao_pedido_criado(estado: dict, dados: dict) -> list:
    pedido_id, produto, quantidade = dados["pedido_id"], dados["produto"], dados["quantidade"]

    if pedido_id in estado["reservas"]:
        return []  # idempotência: este pedido já foi processado

    disponivel = estado["disponivel"].get(produto, 0)
    if quantidade > disponivel:
        return [evento("EstoqueIndisponivel", pedido_id=pedido_id, produto=produto,
                       quantidade=quantidade, disponivel=disponivel)]

    estado["disponivel"][produto] = disponivel - quantidade
    estado["reservas"][pedido_id] = {"produto": produto, "quantidade": quantidade, "status": "RESERVADA"}

    # A mensagem segue adiante levando o que o próximo participante precisa.
    return [evento("EstoqueReservado", pedido_id=pedido_id, cliente=dados["cliente"], produto=produto,
                   quantidade=quantidade, valor_total=dados["valor_total"])]


# ---------------------------------------------------------------------------
# Etapa 4: a transação de COMPENSAÇÃO
# ---------------------------------------------------------------------------
def ao_pagamento_recusado(estado: dict, dados: dict) -> list:
    # TODO (Etapa 4): desfaça a reserva feita em ao_pedido_criado.
    #   1. Busque a reserva pelo id de correlação: estado["reservas"].get(dados["pedido_id"])
    #   2. Se não existe ou o status não é "RESERVADA", devolva [] (nada a compensar).
    #   3. Devolva a quantidade a estado["disponivel"][produto] e marque o status "LIBERADA".
    #   4. Devolva [evento("EstoqueLiberado", pedido_id=..., produto=..., quantidade=...)]
    raise NotImplementedError("Etapa 4: implemente ao_pagamento_recusado em servicos/estoque/estoque.py")


TRATADORES = {
    "PedidoCriado": ao_pedido_criado,
    "PagamentoRecusado": ao_pagamento_recusado,
}
