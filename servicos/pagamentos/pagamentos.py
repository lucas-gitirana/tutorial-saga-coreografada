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

    if pedido_id in estado["pagamentos"]:
        return []  # idempotência: este pedido já foi cobrado (ou recusado)

    saldo = estado["saldos"].get(cliente, 0.0)
    if saldo < valor:
        estado["pagamentos"][pedido_id] = {"cliente": cliente, "valor": valor, "status": "RECUSADO"}
        return [evento("PagamentoRecusado", pedido_id=pedido_id, cliente=cliente, valor_total=valor,
                       motivo=f"saldo insuficiente (saldo {saldo:.2f}, valor {valor:.2f})")]

    estado["saldos"][cliente] = round(saldo - valor, 2)
    estado["pagamentos"][pedido_id] = {"cliente": cliente, "valor": valor, "status": "APROVADO"}
    return [evento("PagamentoAprovado", pedido_id=pedido_id, cliente=cliente, valor_total=valor)]


TRATADORES = {
    "EstoqueReservado": ao_estoque_reservado,
}
