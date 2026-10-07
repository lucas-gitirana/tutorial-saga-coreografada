"""Etapa 2: a primeira saga começou (pedido da ana)."""
from saga import PEDIDOS
from verificador import executar, http, verificacao


@verificacao("existe um pedido da cliente 'ana' no serviço pedidos")
def pedido_da_ana():
    _, pedidos = http("GET", f"{PEDIDOS}/pedidos")
    assert any(p.get("cliente") == "ana" for p in pedidos), (
        "nenhum pedido da 'ana' ainda. Clique em ▶ Executar no bloco 'curl -s -X POST ...' desta etapa."
    )


executar()
