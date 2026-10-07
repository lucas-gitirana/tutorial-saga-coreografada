"""Etapa 6: pagamentos idempotente (o mesmo evento duas vezes não cobra duas vezes)."""
import copy
import time

import saga
from verificador import executar, http, importar, verificacao

pagamentos = importar("servicos/pagamentos", "pagamentos")

RESERVADO = {"pedido_id": "p1", "cliente": "ana", "produto": "teclado", "quantidade": 2, "valor_total": 300.0}


@verificacao("o mesmo EstoqueReservado entregue duas vezes cobra só uma vez")
def cobra_uma_vez():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    assert estado["saldos"]["ana"] == 700.0, (
        f"a ana foi cobrada duas vezes (saldo {estado['saldos']['ana']}). "
        "Escreva o `if pedido_id in estado[\"pagamentos\"]:` no marcador da Etapa 6."
    )


@verificacao("na segunda entrega, nenhum evento é publicado (devolve [])")
def nao_publica():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    segunda = pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    assert segunda == [], f"a segunda entrega devolveu {segunda!r}; deveria devolver []."


@verificacao("o pagamentos em execução ignora uma reentrega (o saldo não muda)")
def ponta_a_ponta():
    cliente = saga.cliente_novo()
    saga.depositar(cliente, 200.0)
    saga.repor("mouse", 1)
    pedido_id = saga.pedir(cliente, "mouse", 1)
    pedido = saga.aguardar_desfecho(pedido_id)
    assert pedido.get("status") == "CONFIRMADO", f"o pedido de teste ficou {pedido.get('status')}."
    status, corpo = http("POST", f"{saga.PAGAMENTOS}/simular/reentrega/{pedido_id}")
    assert status == 202, f"a simulação de reentrega devolveu HTTP {status}: {corpo}"
    time.sleep(2)
    assert saga.saldo(cliente) == 120.0, (
        f"depois da reentrega o saldo foi para {saga.saldo(cliente)} (esperado 120). {saga.dica_logs('pagamentos')}"
    )


executar(parar_na_primeira_falha=True)
