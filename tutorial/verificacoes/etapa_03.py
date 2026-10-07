"""Etapa 3: a saga da ana chegou até o EstoqueReservado."""
from saga import PEDIDOS, aguardar_evento
from verificador import executar, http, verificacao


@verificacao("o estoque reagiu ao pedido da 'ana' publicando EstoqueReservado")
def estoque_reagiu():
    _, pedidos = http("GET", f"{PEDIDOS}/pedidos")
    ids = [p["pedido_id"] for p in pedidos if p.get("cliente") == "ana"]
    assert ids, "nenhum pedido da 'ana'. Volte à Etapa 2 e crie o pedido."
    assert aguardar_evento(ids[0], "EstoqueReservado", segundos=6), (
        f"o EstoqueReservado do pedido {ids[0]} não aparece no histórico. "
        "Veja os logs: docker compose logs estoque --tail 20"
    )


executar()
