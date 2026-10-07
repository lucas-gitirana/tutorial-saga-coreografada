"""Atalhos das verificações de ponta a ponta (com os containers rodando)."""
import uuid

from verificador import aguardar, http

PEDIDOS, ESTOQUE, PAGAMENTOS = "http://localhost:8031", "http://localhost:8032", "http://localhost:8033"


def cliente_novo() -> str:
    """Um cliente que ainda não existe (carteira vazia), para não mexer nos dados do aluno."""
    return f"verif-{uuid.uuid4().hex[:6]}"


def depositar(cliente: str, valor: float) -> None:
    http("POST", f"{PAGAMENTOS}/carteiras/{cliente}/deposito", {"valor": valor})


def repor(produto: str, quantidade: int) -> None:
    http("POST", f"{ESTOQUE}/estoque/{produto}/reposicao", {"quantidade": quantidade})


def saldo(cliente: str) -> float:
    return http("GET", f"{PAGAMENTOS}/carteiras")[1]["saldos"].get(cliente, 0.0)


def disponivel(produto: str) -> int:
    return http("GET", f"{ESTOQUE}/estoque")[1]["disponivel"].get(produto, 0)


def pedir(cliente: str, produto: str, quantidade: int) -> str:
    status, corpo = http("POST", f"{PEDIDOS}/pedidos", {"cliente": cliente, "produto": produto, "quantidade": quantidade})
    assert status == 202, f"POST /pedidos devolveu HTTP {status}: {corpo}"
    return corpo["pedido_id"]


def pedido(pedido_id: str) -> dict:
    return http("GET", f"{PEDIDOS}/pedidos/{pedido_id}")[1]


def historico(pedido_id: str) -> str:
    status, texto = http("GET", f"{PEDIDOS}/pedidos/{pedido_id}/historico")
    return texto if status == 200 else ""


def aguardar_desfecho(pedido_id: str, segundos: float = 10) -> dict:
    """Espera o pedido sair de PENDENTE e devolve o pedido (ou o último estado visto)."""
    aguardar(lambda: pedido(pedido_id).get("status") != "PENDENTE", segundos=segundos)
    return pedido(pedido_id)


def aguardar_evento(pedido_id: str, tipo: str, segundos: float = 10) -> bool:
    return bool(aguardar(lambda: tipo in historico(pedido_id), segundos=segundos))


def dica_logs(servico: str) -> str:
    return (f"O arquivo foi salvo? Veja se o serviço reiniciou sem erro: docker compose logs {servico} --tail 20")
