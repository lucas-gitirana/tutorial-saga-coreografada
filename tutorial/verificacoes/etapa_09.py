"""Etapa 9: compensação no estoque (liberar a reserva)."""
import copy

import saga
from verificador import aguardar, executar, importar, verificacao

estoque = importar("servicos/estoque", "estoque")

CRIADO = {"pedido_id": "p1", "cliente": "bruno", "produto": "teclado", "quantidade": 3, "valor_total": 450.0}
RECUSADO = {"pedido_id": "p1", "cliente": "bruno", "valor_total": 450.0, "motivo": "saldo insuficiente"}


def reservado():
    estado = copy.deepcopy(estoque.ESTADO_INICIAL)
    estoque.ao_pedido_criado(estado, dict(CRIADO))  # 10 teclados -> 7 (e a reserva p1)
    return estado


@verificacao("PagamentoRecusado devolve ao estoque a quantidade reservada (7 → 10 teclados)")
def devolve():
    estado = reservado()
    estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    assert estado["disponivel"]["teclado"] == 10, (
        f"esperado 10 teclados depois da compensação, há {estado['disponivel']['teclado']}."
    )


@verificacao("a reserva é marcada como LIBERADA e a função devolve [EstoqueLiberado]")
def libera():
    estado = reservado()
    eventos = estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    assert estado["reservas"]["p1"]["status"] == "LIBERADA", f"status da reserva: {estado['reservas']['p1']['status']!r}."
    assert eventos is not None, "a função não devolveu nada. Termine com return [evento(\"EstoqueLiberado\", ...)]."
    assert [e.get("tipo") for e in eventos] == ["EstoqueLiberado"], f"eventos devolvidos: {eventos}"
    dados = eventos[0]["dados"]
    assert (dados.get("pedido_id"), dados.get("produto"), dados.get("quantidade")) == ("p1", "teclado", 3), (
        f"o EstoqueLiberado deveria levar pedido_id, produto e quantidade; veio {dados}."
    )


@verificacao("compensar duas vezes não devolve o estoque duas vezes")
def idempotente():
    estado = reservado()
    estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    segunda = estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    assert estado["disponivel"]["teclado"] == 10, f"estoque devolvido duas vezes: {estado['disponivel']['teclado']} teclados."
    assert segunda == [], f"a segunda compensação devolveu {segunda!r}; deveria devolver []."


@verificacao("pedido sem reserva é ignorado sem erro")
def sem_reserva():
    estado = copy.deepcopy(estoque.ESTADO_INICIAL)
    assert estoque.ao_pagamento_recusado(estado, dict(RECUSADO, pedido_id="nao-existe")) == []


@verificacao("o estoque em execução compensa a reserva de um pedido sem saldo")
def ponta_a_ponta():
    saga.repor("teclado", 1)
    antes = saga.disponivel("teclado")
    pedido_id = saga.pedir(saga.cliente_novo(), "teclado", 1)
    assert saga.aguardar_evento(pedido_id, "EstoqueLiberado"), (
        f"o pedido {pedido_id} não recebeu EstoqueLiberado. {saga.dica_logs('estoque')}"
    )
    assert aguardar(lambda: saga.disponivel("teclado") == antes, segundos=5), (
        f"havia {antes} teclados antes do pedido e agora há {saga.disponivel('teclado')}."
    )


executar(parar_na_primeira_falha=True)
