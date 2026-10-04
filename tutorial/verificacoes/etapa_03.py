"""Etapa 3: desfechos de falha no serviço de pedidos (testado sem subir containers)."""
from verificador import executar, importar, verificacao

pedidos = importar("servicos/pedidos", "pedidos")


def novo_pedido():
    estado = {"pedidos": {}}
    pedido, _ = pedidos.criar_pedido(estado, "ana", "teclado", 1)
    return estado, pedido["pedido_id"]


def tipos(eventos):
    return [e.get("tipo") for e in eventos or []]


@verificacao("EstoqueIndisponivel: pedido CANCELADO com motivo e evento PedidoCancelado")
def estoque_indisponivel():
    estado, pid = novo_pedido()
    eventos = pedidos.ao_estoque_indisponivel(estado, {"pedido_id": pid, "produto": "teclado",
                                                      "quantidade": 1, "disponivel": 0})
    pedido = estado["pedidos"][pid]
    assert pedido["status"] == "CANCELADO", f"status: {pedido['status']!r}."
    assert "estoque" in str(pedido.get("motivo", "")).lower(), "preencha pedido['motivo'] (ex.: 'estoque indisponível')."
    assert tipos(eventos) == ["PedidoCancelado"], f"eventos publicados: {tipos(eventos)}."
    assert eventos[0]["dados"].get("pedido_id") == pid, "o PedidoCancelado precisa levar o pedido_id."


@verificacao("PagamentoRecusado: pedido CANCELADO com o motivo vindo do evento")
def pagamento_recusado():
    estado, pid = novo_pedido()
    eventos = pedidos.ao_pagamento_recusado(estado, {"pedido_id": pid, "cliente": "ana", "valor_total": 150.0,
                                                    "motivo": "saldo insuficiente"})
    pedido = estado["pedidos"][pid]
    assert pedido["status"] == "CANCELADO", f"status: {pedido['status']!r}."
    assert pedido.get("motivo") == "saldo insuficiente", f"motivo: {pedido.get('motivo')!r} (use dados['motivo'])."
    assert tipos(eventos) == ["PedidoCancelado"], f"eventos publicados: {tipos(eventos)}."


@verificacao("pedido que já teve desfecho (não está PENDENTE) não muda e não publica nada")
def ja_finalizado():
    estado, pid = novo_pedido()
    pedidos.ao_pagamento_aprovado(estado, {"pedido_id": pid})
    eventos = (pedidos.ao_pagamento_recusado(estado, {"pedido_id": pid, "motivo": "x"}) or []) + \
        (pedidos.ao_estoque_indisponivel(estado, {"pedido_id": pid}) or [])
    assert estado["pedidos"][pid]["status"] == "CONFIRMADO", "um pedido CONFIRMADO não pode virar CANCELADO."
    assert not eventos, "nenhum evento deveria ser publicado para um pedido que não está PENDENTE."


@verificacao("pedido desconhecido é ignorado sem erro")
def desconhecido():
    estado, _ = novo_pedido()
    assert not pedidos.ao_pagamento_recusado(estado, {"pedido_id": "nao-existe", "motivo": "x"})
    assert not pedidos.ao_estoque_indisponivel(estado, {"pedido_id": "nao-existe"})


executar()
