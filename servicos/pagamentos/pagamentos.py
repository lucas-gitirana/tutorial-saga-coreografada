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
    """evento("X", a=1) devolve {"tipo": "X", "dados": {"a": 1}}."""
    return {"tipo": tipo, "dados": dados}


# ---------------------------------------------------------------------------
# Etapas 4, 5 e 6: a transação local do pagamento
# ---------------------------------------------------------------------------
def ao_estoque_reservado(estado: dict, dados: dict) -> list:
    pedido_id = dados["pedido_id"]               # id de correlação, ex.: "ana-1"
    cliente = dados["cliente"]                   # ex.: "ana"
    valor = dados["valor_total"]                 # ex.: 300.0
    saldo = estado["saldos"].get(cliente, 0.0)   # quanto o cliente tem na carteira

    # ═══ Etapa 6 · IDEMPOTÊNCIA: este pedido já foi cobrado? ═══════════════
    # ✏️  Escreva aqui o `if` que ignora um evento repetido.



    # ═══ Etapa 5 · SALDO INSUFICIENTE: recusar ═════════════════════════════
    # ✏️  Escreva aqui o `if` que recusa o pagamento.



    # ═══ Etapa 4 · SALDO SUFICIENTE: cobrar e aprovar ══════════════════════
    # ✏️  Escreva aqui as 3 linhas: debitar, registrar e devolver o evento.



TRATADORES = {
    "EstoqueReservado": ao_estoque_reservado,
}
