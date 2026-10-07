"""Etapa 8: pedidos reage ao PagamentoRecusado."""
import saga
from verificador import executar, importar, verificacao

pedidos = importar("servicos/pedidos", "pedidos")
RECUSADO = {"cliente": "bruno", "valor_total": 900.0, "motivo": "saldo insuficiente"}


def novo_pedido():
    estado = {"pedidos": {}}
    pedido, _ = pedidos.criar_pedido(estado, "bruno", "monitor", 1)
    return estado, pedido["pedido_id"]


@verificacao("PagamentoRecusado: o pedido fica CANCELADO com o motivo vindo do evento")
def cancela():
    estado, pid = novo_pedido()
    pedidos.ao_pagamento_recusado(estado, dict(RECUSADO, pedido_id=pid, motivo="cartão bloqueado"))
    pedido = estado["pedidos"][pid]
    assert pedido["status"] == "CANCELADO", f"status: {pedido['status']!r} (esperado 'CANCELADO')."
    assert pedido.get("motivo") == "cartão bloqueado", (
        f"motivo: {pedido.get('motivo')!r}. O motivo deve vir do evento: dados[\"motivo\"]."
    )


@verificacao("devolve [PedidoCancelado] com o pedido_id")
def publica():
    estado, pid = novo_pedido()
    eventos = pedidos.ao_pagamento_recusado(estado, dict(RECUSADO, pedido_id=pid))
    assert eventos is not None, "a função não devolveu nada. Termine com return [evento(\"PedidoCancelado\", ...)]."
    assert [e.get("tipo") for e in eventos] == ["PedidoCancelado"], f"eventos devolvidos: {eventos}"
    assert eventos[0]["dados"].get("pedido_id") == pid, "o PedidoCancelado precisa levar o pedido_id."


@verificacao("pedido desconhecido ou que já teve desfecho: devolve [] sem mudar nada")
def ignora():
    estado, pid = novo_pedido()
    pedidos.ao_pagamento_aprovado(estado, {"pedido_id": pid})
    assert pedidos.ao_pagamento_recusado(estado, dict(RECUSADO, pedido_id=pid)) == [], (
        "um pedido CONFIRMADO não pode ser cancelado. Comece com: if pedido is None: return []"
    )
    assert estado["pedidos"][pid]["status"] == "CONFIRMADO"
    assert pedidos.ao_pagamento_recusado(estado, dict(RECUSADO, pedido_id="nao-existe")) == []


@verificacao("o pedidos em execução cancela um pedido sem saldo")
def ponta_a_ponta():
    saga.repor("mouse", 1)
    pedido = saga.aguardar_desfecho(saga.pedir(saga.cliente_novo(), "mouse", 1))
    assert pedido.get("status") == "CANCELADO", (
        f"o pedido {pedido.get('pedido_id')} ficou {pedido.get('status')}. {saga.dica_logs('pedidos')}"
    )
    assert "saldo" in str(pedido.get("motivo") or "").lower(), f"motivo do cancelamento: {pedido.get('motivo')!r}."


executar(parar_na_primeira_falha=True)
