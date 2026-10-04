"""Etapa 4: compensação no estoque (testado sem subir containers)."""
import copy

from verificador import executar, importar, verificacao

estoque = importar("servicos/estoque", "estoque")

CRIADO = {"pedido_id": "p1", "cliente": "ana", "produto": "teclado", "quantidade": 3, "valor_total": 450.0}
RECUSADO = {"pedido_id": "p1", "cliente": "ana", "valor_total": 450.0, "motivo": "saldo insuficiente"}


def reservado():
    estado = copy.deepcopy(estoque.ESTADO_INICIAL)
    estado["disponivel"]["teclado"] = 10
    estoque.ao_pedido_criado(estado, dict(CRIADO))
    assert estado["disponivel"]["teclado"] == 7, "pré-requisito: a reserva de exemplo deveria deixar 7 teclados."
    return estado


@verificacao("PagamentoRecusado devolve ao estoque a quantidade reservada")
def devolve():
    estado = reservado()
    estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    assert estado["disponivel"]["teclado"] == 10, (
        f"esperado 10 teclados disponíveis após a compensação, há {estado['disponivel']['teclado']}."
    )


@verificacao("a reserva é marcada como LIBERADA e o evento EstoqueLiberado é publicado")
def libera():
    estado = reservado()
    eventos = estoque.ao_pagamento_recusado(estado, dict(RECUSADO)) or []
    assert estado["reservas"]["p1"]["status"] == "LIBERADA", f"status da reserva: {estado['reservas']['p1']['status']!r}."
    assert [e.get("tipo") for e in eventos] == ["EstoqueLiberado"], f"eventos publicados: {[e.get('tipo') for e in eventos]}."
    dados = eventos[0]["dados"]
    assert dados.get("pedido_id") == "p1" and dados.get("produto") == "teclado" and dados.get("quantidade") == 3, (
        f"o EstoqueLiberado deveria levar pedido_id, produto e quantidade; veio {dados}."
    )


@verificacao("idempotência: compensar duas vezes não devolve o estoque duas vezes")
def idempotente():
    estado = reservado()
    estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    segunda = estoque.ao_pagamento_recusado(estado, dict(RECUSADO))
    assert estado["disponivel"]["teclado"] == 10, f"estoque devolvido duas vezes: {estado['disponivel']['teclado']} teclados."
    assert not segunda, "na segunda entrega, nenhum evento deveria ser publicado."


@verificacao("pedido sem reserva (desconhecido) é ignorado sem erro")
def sem_reserva():
    estado = copy.deepcopy(estoque.ESTADO_INICIAL)
    assert not estoque.ao_pagamento_recusado(estado, dict(RECUSADO, pedido_id="nao-existe"))


executar()
