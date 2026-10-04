"""Regras do serviço de PAGAMENTOS: cobra o cliente depois da reserva.

  EstoqueReservado -> debita da carteira -> PagamentoAprovado | PagamentoRecusado

Funções puras: recebem o estado do serviço e os dados do evento e devolvem a
lista de eventos a publicar.
"""
from __future__ import annotations

ESTADO_INICIAL = {
    "saldos": {"ana": 1000.0, "bruno": 100.0, "carla": 5000.0},
    "pagamentos": {},  # pedido_id -> {"cliente", "valor", "status": APROVADO | RECUSADO}
}


def evento(tipo: str, **dados) -> dict:
    return {"tipo": tipo, "dados": dados}


# ---------------------------------------------------------------------------
# Etapa 2: a transação local do pagamento
# ---------------------------------------------------------------------------
def ao_estoque_reservado(estado: dict, dados: dict) -> list:
    pedido_id, cliente, valor = dados["pedido_id"], dados["cliente"], dados["valor_total"]

    # TODO (Etapa 2): implemente a transação local do pagamento.
    #   0. Idempotência: se pedido_id já está em estado["pagamentos"], devolva [].
    #   1. Leia o saldo: estado["saldos"].get(cliente, 0.0)
    #   2. Saldo menor que o valor:
    #        - registre estado["pagamentos"][pedido_id] = {"cliente", "valor", "status": "RECUSADO"}
    #        - devolva [evento("PagamentoRecusado", pedido_id=..., cliente=..., valor_total=...,
    #                          motivo="saldo insuficiente")]
    #   3. Senão:
    #        - debite o valor de estado["saldos"][cliente]
    #        - registre estado["pagamentos"][pedido_id] com "status": "APROVADO"
    #        - devolva [evento("PagamentoAprovado", pedido_id=..., cliente=..., valor_total=...)]
    raise NotImplementedError("Etapa 2: implemente ao_estoque_reservado em servicos/pagamentos/pagamentos.py")


TRATADORES = {
    "EstoqueReservado": ao_estoque_reservado,
}
