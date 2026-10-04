"""Etapa 1: ambiente no ar e primeira saga iniciada."""
from verificador import executar, http, verificacao

SERVICOS = {"pedidos": 8031, "estoque": 8032, "pagamentos": 8033}

for nome, porta in SERVICOS.items():
    def checar(porta=porta):
        status, _ = http("GET", f"http://localhost:{porta}/saude")
        assert status == 200, f"/saude devolveu HTTP {status}."
    verificacao(f"{nome} responde em http://localhost:{porta}/saude")(checar)


@verificacao("ao menos um pedido foi criado")
def pedido_criado():
    _, pedidos = http("GET", "http://localhost:8031/pedidos")
    assert pedidos, "nenhum pedido ainda. Rode o comando 'curl -X POST .../pedidos' desta etapa."


executar(parar_na_primeira_falha=True)
