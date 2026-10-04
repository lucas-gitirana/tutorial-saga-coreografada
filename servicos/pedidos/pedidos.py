"""Regras do serviço de PEDIDOS: inicia a saga e registra o desfecho.

O pedido nasce PENDENTE. Ninguém "manda" o pedido ser confirmado: o serviço
de pedidos apenas OUVE os eventos dos outros participantes e reage:

  PagamentoAprovado   -> CONFIRMADO
  EstoqueIndisponivel -> CANCELADO
  PagamentoRecusado   -> CANCELADO

Funções puras: recebem o estado do serviço e os dados do evento e devolvem a
lista de eventos a publicar.
"""
from __future__ import annotations

import uuid

PRECOS = {"teclado": 150.0, "mouse": 80.0, "monitor": 900.0}

ESTADO_INICIAL = {"pedidos": {}}


class ErroDePedido(Exception):
    pass


def evento(tipo: str, **dados) -> dict:
    return {"tipo": tipo, "dados": dados}


def criar_pedido(estado: dict, cliente: str, produto: str, quantidade: int) -> tuple[dict, list]:
    """Inicia a saga: grava o pedido PENDENTE e publica PedidoCriado."""
    if not cliente:
        raise ErroDePedido("O campo 'cliente' é obrigatório.")
    if produto not in PRECOS:
        raise ErroDePedido(f"Produto desconhecido. Use um destes: {', '.join(PRECOS)}.")
    if not isinstance(quantidade, int) or quantidade <= 0:
        raise ErroDePedido("A 'quantidade' deve ser um inteiro maior que zero.")

    pedido = {
        "pedido_id": uuid.uuid4().hex[:8],  # id de correlação: acompanha todos os eventos da saga
        "cliente": cliente,
        "produto": produto,
        "quantidade": quantidade,
        "valor_total": round(PRECOS[produto] * quantidade, 2),
        "status": "PENDENTE",
        "motivo": None,
    }
    estado["pedidos"][pedido["pedido_id"]] = pedido
    return pedido, [evento("PedidoCriado", **{k: pedido[k] for k in
                                               ("pedido_id", "cliente", "produto", "quantidade", "valor_total")})]


def _pedido_pendente(estado: dict, dados: dict) -> dict | None:
    """Devolve o pedido se ele existe e ainda está PENDENTE; senão None.
    (Evita processar duas vezes o mesmo desfecho: idempotência.)"""
    pedido = estado["pedidos"].get(dados["pedido_id"])
    if pedido is None or pedido["status"] != "PENDENTE":
        return None
    return pedido


# ---------------------------------------------------------------------------
# Exemplo pronto: o caminho feliz
# ---------------------------------------------------------------------------
def ao_pagamento_aprovado(estado: dict, dados: dict) -> list:
    pedido = _pedido_pendente(estado, dados)
    if pedido is None:
        return []
    pedido["status"] = "CONFIRMADO"
    return [evento("PedidoConfirmado", pedido_id=pedido["pedido_id"])]


# ---------------------------------------------------------------------------
# Etapa 3: os caminhos de falha
# ---------------------------------------------------------------------------
def ao_estoque_indisponivel(estado: dict, dados: dict) -> list:
    # TODO (Etapa 3): siga o exemplo de ao_pagamento_aprovado, logo acima.
    #   - use _pedido_pendente(estado, dados): se devolver None, devolva []
    #   - status "CANCELADO" e motivo "estoque indisponível"
    #   - devolva [evento("PedidoCancelado", pedido_id=..., motivo=...)]
    raise NotImplementedError("Etapa 3: implemente ao_estoque_indisponivel em servicos/pedidos/pedidos.py")


def ao_pagamento_recusado(estado: dict, dados: dict) -> list:
    # TODO (Etapa 3): igual ao anterior, mas o motivo vem do evento: dados["motivo"]
    raise NotImplementedError("Etapa 3: implemente ao_pagamento_recusado em servicos/pedidos/pedidos.py")


TRATADORES = {
    "PagamentoAprovado": ao_pagamento_aprovado,
    "EstoqueIndisponivel": ao_estoque_indisponivel,
    "PagamentoRecusado": ao_pagamento_recusado,
}
