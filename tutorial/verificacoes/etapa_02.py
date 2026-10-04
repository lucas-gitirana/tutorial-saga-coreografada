"""Etapa 2: participante pagamentos (testado sem subir containers)."""
import copy

from verificador import executar, importar, verificacao

pagamentos = importar("servicos/pagamentos", "pagamentos")

RESERVADO = {"pedido_id": "p1", "cliente": "ana", "produto": "teclado", "quantidade": 2, "valor_total": 300.0}


def estado(saldo_ana=1000.0):
    e = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    e["saldos"]["ana"] = saldo_ana
    return e


@verificacao("saldo suficiente: debita o valor e publica PagamentoAprovado")
def aprova():
    e = estado(1000.0)
    eventos = pagamentos.ao_estoque_reservado(e, dict(RESERVADO))
    assert e["saldos"]["ana"] == 700.0, f"saldo da ana deveria ir de 1000 para 700, está {e['saldos']['ana']}."
    assert [ev.get("tipo") for ev in eventos or []] == ["PagamentoAprovado"], (
        f"esperado [PagamentoAprovado], veio {[ev.get('tipo') for ev in eventos or []]}."
    )
    dados = eventos[0]["dados"]
    assert dados.get("pedido_id") == "p1", "o evento precisa levar o pedido_id (id de correlação)."
    assert dados.get("cliente") == "ana" and dados.get("valor_total") == 300.0, f"dados do evento: {dados}"
    assert e["pagamentos"].get("p1", {}).get("status") == "APROVADO", (
        "registre o pagamento em estado['pagamentos']['p1'] com status 'APROVADO'."
    )


@verificacao("saldo insuficiente: NÃO debita e publica PagamentoRecusado com um motivo")
def recusa():
    e = estado(100.0)
    eventos = pagamentos.ao_estoque_reservado(e, dict(RESERVADO))
    assert e["saldos"]["ana"] == 100.0, "o saldo não pode mudar quando o pagamento é recusado."
    assert [ev.get("tipo") for ev in eventos or []] == ["PagamentoRecusado"], (
        f"esperado [PagamentoRecusado], veio {[ev.get('tipo') for ev in eventos or []]}."
    )
    dados = eventos[0]["dados"]
    assert dados.get("pedido_id") == "p1", "o evento precisa levar o pedido_id (id de correlação)."
    assert "saldo" in str(dados.get("motivo", "")).lower(), "inclua em 'motivo' um texto explicando (ex.: 'saldo insuficiente')."
    assert e["pagamentos"].get("p1", {}).get("status") == "RECUSADO", (
        "registre o pagamento em estado['pagamentos']['p1'] com status 'RECUSADO'."
    )


@verificacao("cliente sem carteira é tratado como saldo zero (recusa, sem erro)")
def sem_carteira():
    e = estado()
    eventos = pagamentos.ao_estoque_reservado(e, dict(RESERVADO, cliente="desconhecido"))
    assert [ev.get("tipo") for ev in eventos or []] == ["PagamentoRecusado"], "use estado['saldos'].get(cliente, 0.0)."


@verificacao("idempotência: o mesmo evento entregue duas vezes não cobra duas vezes")
def idempotente():
    e = estado(1000.0)
    pagamentos.ao_estoque_reservado(e, dict(RESERVADO))
    segunda = pagamentos.ao_estoque_reservado(e, dict(RESERVADO))
    assert e["saldos"]["ana"] == 700.0, f"o cliente foi cobrado duas vezes (saldo {e['saldos']['ana']})."
    assert not segunda, "na segunda entrega, nenhum evento deveria ser publicado."


executar()
