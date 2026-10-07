"""Etapa 7: pedidos reage ao EstoqueIndisponivel."""
import saga
from verificador import executar, importar, verificacao

pedidos = importar("servicos/pedidos", "pedidos")
INDISPONIVEL = {"produto": "monitor", "quantidade": 5, "disponivel": 2}


def novo_pedido():
    estado = {"pedidos": {}}
    pedido, _ = pedidos.criar_pedido(estado, "carla", "monitor", 5)
    return estado, pedido["pedido_id"]


@verificacao("EstoqueIndisponivel: o pedido fica CANCELADO com motivo 'estoque indisponível'")
def cancela():
    estado, pid = novo_pedido()
    pedidos.ao_estoque_indisponivel(estado, dict(INDISPONIVEL, pedido_id=pid))
    pedido = estado["pedidos"][pid]
    assert pedido["status"] == "CANCELADO", f"status: {pedido['status']!r} (esperado 'CANCELADO')."
    assert "estoque" in str(pedido.get("motivo") or "").lower(), f"motivo: {pedido.get('motivo')!r}."


@verificacao("devolve [PedidoCancelado] com o pedido_id")
def publica():
    estado, pid = novo_pedido()
    eventos = pedidos.ao_estoque_indisponivel(estado, dict(INDISPONIVEL, pedido_id=pid))
    assert eventos is not None, "a função não devolveu nada. Termine com return [evento(\"PedidoCancelado\", ...)]."
    assert [e.get("tipo") for e in eventos] == ["PedidoCancelado"], f"eventos devolvidos: {eventos}"
    assert eventos[0]["dados"].get("pedido_id") == pid, "o PedidoCancelado precisa levar o pedido_id."


@verificacao("pedido desconhecido ou que já teve desfecho: devolve [] sem mudar nada")
def ignora():
    estado, pid = novo_pedido()
    pedidos.ao_pagamento_aprovado(estado, {"pedido_id": pid})
    assert pedidos.ao_estoque_indisponivel(estado, dict(INDISPONIVEL, pedido_id=pid)) == [], (
        "um pedido CONFIRMADO não pode ser cancelado. Comece com: if pedido is None: return []"
    )
    assert estado["pedidos"][pid]["status"] == "CONFIRMADO"
    assert pedidos.ao_estoque_indisponivel(estado, dict(INDISPONIVEL, pedido_id="nao-existe")) == []


@verificacao("o pedidos em execução cancela um pedido sem estoque")
def ponta_a_ponta():
    pedido = saga.aguardar_desfecho(saga.pedir(saga.cliente_novo(), "monitor", 999))
    assert pedido.get("status") == "CANCELADO", (
        f"o pedido {pedido.get('pedido_id')} ficou {pedido.get('status')}. {saga.dica_logs('pedidos')}"
    )


executar(parar_na_primeira_falha=True)
