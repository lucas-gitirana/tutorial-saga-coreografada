"""Etapa 10: a saga completa, ponta a ponta (containers rodando)."""
import saga
from verificador import aguardar, executar, verificacao

contexto = {}


@verificacao("caminho feliz: pedido CONFIRMADO, estoque baixado e cliente cobrado")
def feliz():
    cliente = saga.cliente_novo()
    saga.depositar(cliente, 200.0)
    saga.repor("mouse", 1)
    antes = saga.disponivel("mouse")
    pedido = saga.aguardar_desfecho(saga.pedir(cliente, "mouse", 1), segundos=15)
    assert pedido["status"] == "CONFIRMADO", f"esperado CONFIRMADO, veio {pedido['status']} ({pedido.get('motivo')})."
    assert saga.disponivel("mouse") == antes - 1, "o estoque de mouse deveria ter diminuído 1."
    assert saga.saldo(cliente) == 120.0, f"o saldo do cliente deveria ser 200 - 80 = 120, é {saga.saldo(cliente)}."


@verificacao("sem saldo: pedido CANCELADO e a reserva COMPENSADA (estoque devolvido)")
def sem_saldo():
    saga.repor("teclado", 1)
    antes = saga.disponivel("teclado")
    pedido = saga.aguardar_desfecho(saga.pedir(saga.cliente_novo(), "teclado", 1), segundos=15)
    contexto["compensado"] = pedido["pedido_id"]
    assert pedido["status"] == "CANCELADO", f"esperado CANCELADO, veio {pedido['status']}."
    assert "saldo" in str(pedido.get("motivo") or "").lower(), f"motivo do cancelamento: {pedido.get('motivo')!r}."
    assert aguardar(lambda: saga.disponivel("teclado") == antes, segundos=10), (
        f"o estoque de teclado era {antes} e agora é {saga.disponivel('teclado')}: a reserva não foi compensada."
    )


@verificacao("a linha do tempo da saga compensada tem todos os eventos esperados")
def linha_do_tempo():
    texto = saga.historico(contexto["compensado"])
    for tipo in ("PedidoCriado", "EstoqueReservado", "PagamentoRecusado", "EstoqueLiberado", "PedidoCancelado"):
        assert tipo in texto, f"o evento {tipo} não aparece no histórico:\n{texto}"


@verificacao("sem estoque: pedido CANCELADO e o cliente não é cobrado")
def sem_estoque():
    cliente = saga.cliente_novo()
    saga.depositar(cliente, 100.0)
    pedido = saga.aguardar_desfecho(saga.pedir(cliente, "monitor", 999), segundos=15)
    assert pedido["status"] == "CANCELADO", f"esperado CANCELADO, veio {pedido['status']}."
    assert "estoque" in str(pedido.get("motivo") or "").lower(), f"motivo do cancelamento: {pedido.get('motivo')!r}."
    assert saga.saldo(cliente) == 100.0, "o cliente foi cobrado por um pedido sem estoque."


executar(parar_na_primeira_falha=True)
