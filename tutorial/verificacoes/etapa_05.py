"""Etapa 5: a saga completa, ponta a ponta (containers rodando)."""
import uuid

from verificador import aguardar, executar, http, verificacao

PEDIDOS, ESTOQUE, PAGAMENTOS = "http://localhost:8031", "http://localhost:8032", "http://localhost:8033"
contexto = {}


def disponivel(produto):
    return http("GET", f"{ESTOQUE}/estoque")[1]["disponivel"].get(produto, 0)


def saldo(cliente):
    return http("GET", f"{PAGAMENTOS}/carteiras")[1]["saldos"].get(cliente, 0.0)


def pedir(cliente, produto, quantidade):
    status, corpo = http("POST", f"{PEDIDOS}/pedidos", {"cliente": cliente, "produto": produto, "quantidade": quantidade})
    assert status == 202, f"POST /pedidos devolveu HTTP {status}: {corpo}"
    pid = corpo["pedido_id"]
    final = aguardar(lambda: http("GET", f"{PEDIDOS}/pedidos/{pid}")[1].get("status") != "PENDENTE", segundos=15)
    pedido = http("GET", f"{PEDIDOS}/pedidos/{pid}")[1]
    assert final, (
        f"o pedido {pid} continua PENDENTE após 15s. Algum serviço não reiniciou com o código novo? "
        f"Veja: curl localhost:8031/pedidos/{pid}/historico"
    )
    return pedido


@verificacao("caminho feliz: pedido CONFIRMADO, estoque baixado e cliente cobrado")
def feliz():
    cliente = f"verif-{uuid.uuid4().hex[:6]}"
    http("POST", f"{PAGAMENTOS}/carteiras/{cliente}/deposito", {"valor": 200.0})
    http("POST", f"{ESTOQUE}/estoque/mouse/reposicao", {"quantidade": 1})
    estoque_antes = disponivel("mouse")
    pedido = pedir(cliente, "mouse", 1)
    assert pedido["status"] == "CONFIRMADO", f"esperado CONFIRMADO, veio {pedido['status']} ({pedido.get('motivo')})."
    assert disponivel("mouse") == estoque_antes - 1, "o estoque de mouse deveria ter diminuído 1."
    assert saldo(cliente) == 120.0, f"o saldo do cliente deveria ser 200 - 80 = 120, é {saldo(cliente)}."


@verificacao("sem saldo: pedido CANCELADO e a reserva COMPENSADA (estoque devolvido)")
def sem_saldo():
    cliente = f"verif-{uuid.uuid4().hex[:6]}"  # carteira vazia
    http("POST", f"{ESTOQUE}/estoque/teclado/reposicao", {"quantidade": 1})
    estoque_antes = disponivel("teclado")
    pedido = pedir(cliente, "teclado", 1)
    contexto["pedido_compensado"] = pedido["pedido_id"]
    assert pedido["status"] == "CANCELADO", f"esperado CANCELADO, veio {pedido['status']}."
    assert "saldo" in str(pedido.get("motivo", "")).lower(), f"motivo do cancelamento: {pedido.get('motivo')!r}."
    devolvido = aguardar(lambda: disponivel("teclado") == estoque_antes, segundos=10)
    assert devolvido, (
        f"o estoque de teclado era {estoque_antes} e agora é {disponivel('teclado')}: a reserva não foi compensada."
    )


@verificacao("a linha do tempo da saga compensada tem todos os eventos esperados")
def historico():
    status, texto = http("GET", f"{PEDIDOS}/pedidos/{contexto['pedido_compensado']}/historico")
    assert status == 200, f"HTTP {status}: {texto}"
    for tipo in ("PedidoCriado", "EstoqueReservado", "PagamentoRecusado", "EstoqueLiberado", "PedidoCancelado"):
        assert tipo in texto, f"o evento {tipo} não aparece no histórico:\n{texto}"


@verificacao("sem estoque: pedido CANCELADO e o cliente não é cobrado")
def sem_estoque():
    saldo_antes = saldo("carla")
    pedido = pedir("carla", "monitor", 999)
    assert pedido["status"] == "CANCELADO", f"esperado CANCELADO, veio {pedido['status']}."
    assert "estoque" in str(pedido.get("motivo", "")).lower(), f"motivo do cancelamento: {pedido.get('motivo')!r}."
    assert saldo("carla") == saldo_antes, "a carla foi cobrada por um pedido sem estoque."


executar(parar_na_primeira_falha=True)
