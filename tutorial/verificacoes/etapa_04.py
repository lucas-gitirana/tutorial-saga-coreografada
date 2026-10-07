"""Etapa 4: pagamentos, saldo suficiente (cobrar e aprovar)."""
import copy

import saga
from verificador import executar, importar, verificacao

pagamentos = importar("servicos/pagamentos", "pagamentos")

RESERVADO = {"pedido_id": "p1", "cliente": "ana", "produto": "teclado", "quantidade": 2, "valor_total": 300.0}


@verificacao("saldo suficiente: debita o valor (ana: 1000 → 700)")
def debita():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    assert estado["saldos"]["ana"] == 700.0, (
        f"o saldo da ana deveria ir de 1000 para 700, está {estado['saldos']['ana']}. "
        "Confira a linha estado[\"saldos\"][cliente] = saldo - valor."
    )


@verificacao("registra o pagamento como APROVADO em estado['pagamentos']")
def registra():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    registro = estado["pagamentos"].get("p1")
    assert registro, "estado['pagamentos']['p1'] não foi criado."
    assert registro.get("status") == "APROVADO", f"status do registro: {registro.get('status')!r}."


@verificacao("devolve [PagamentoAprovado] com pedido_id, cliente e valor_total")
def publica():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    eventos = pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    assert eventos is not None, "a função não devolveu nada. Termine com return [evento(\"PagamentoAprovado\", ...)]."
    assert [e.get("tipo") for e in eventos] == ["PagamentoAprovado"], f"eventos devolvidos: {eventos}"
    dados = eventos[0]["dados"]
    esperado = {"pedido_id": "p1", "cliente": "ana", "valor_total": 300.0}
    for campo, valor in esperado.items():
        assert dados.get(campo) == valor, f"dados['{campo}'] deveria ser {valor!r}, veio {dados.get(campo)!r}."


@verificacao("o pagamentos em execução já usa o seu código (um pedido novo é CONFIRMADO)")
def ponta_a_ponta():
    cliente = saga.cliente_novo()
    saga.depositar(cliente, 200.0)
    saga.repor("mouse", 1)
    pedido = saga.aguardar_desfecho(saga.pedir(cliente, "mouse", 1))
    assert pedido.get("status") == "CONFIRMADO", (
        f"o pedido {pedido.get('pedido_id')} ficou {pedido.get('status')}. {saga.dica_logs('pagamentos')}"
    )


executar(parar_na_primeira_falha=True)
