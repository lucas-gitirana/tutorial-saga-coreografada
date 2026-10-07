"""Etapa 5: pagamentos, saldo insuficiente (recusar)."""
import copy

import saga
from verificador import executar, importar, verificacao

pagamentos = importar("servicos/pagamentos", "pagamentos")

RESERVADO = {"pedido_id": "p1", "cliente": "bruno", "produto": "monitor", "quantidade": 1, "valor_total": 900.0}


def tipos(eventos):
    return [e.get("tipo") for e in eventos or []]


@verificacao("saldo insuficiente: o saldo NÃO muda (bruno continua com 100)")
def nao_debita():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    assert estado["saldos"]["bruno"] == 100.0, (
        f"o saldo do bruno virou {estado['saldos']['bruno']}. O `if saldo < valor:` precisa vir ANTES do código da Etapa 4."
    )


@verificacao("registra o pagamento como RECUSADO e devolve [PagamentoRecusado] com um motivo")
def recusa():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    eventos = pagamentos.ao_estoque_reservado(estado, dict(RESERVADO))
    assert estado["pagamentos"].get("p1", {}).get("status") == "RECUSADO", (
        f"estado['pagamentos']['p1'] = {estado['pagamentos'].get('p1')!r} (o status deveria ser 'RECUSADO')."
    )
    assert tipos(eventos) == ["PagamentoRecusado"], f"eventos devolvidos: {tipos(eventos)}."
    dados = eventos[0]["dados"]
    assert dados.get("pedido_id") == "p1", "o evento precisa levar o pedido_id (id de correlação)."
    assert "saldo" in str(dados.get("motivo") or "").lower(), (
        f"motivo: {dados.get('motivo')!r}. Use um texto como 'saldo insuficiente'."
    )


@verificacao("cliente sem carteira é tratado como saldo zero (recusa, sem erro)")
def sem_carteira():
    estado = copy.deepcopy(pagamentos.ESTADO_INICIAL)
    eventos = pagamentos.ao_estoque_reservado(estado, dict(RESERVADO, cliente="desconhecido"))
    assert tipos(eventos) == ["PagamentoRecusado"], f"eventos devolvidos: {tipos(eventos)}."


@verificacao("o pagamentos em execução já recusa um pedido sem saldo (PagamentoRecusado no histórico)")
def ponta_a_ponta():
    saga.repor("mouse", 1)
    pedido_id = saga.pedir(saga.cliente_novo(), "mouse", 1)  # cliente novo: carteira vazia
    assert saga.aguardar_evento(pedido_id, "PagamentoRecusado"), (
        f"o pedido {pedido_id} não recebeu PagamentoRecusado. {saga.dica_logs('pagamentos')}"
    )


executar(parar_na_primeira_falha=True)
