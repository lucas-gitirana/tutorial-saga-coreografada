"""Etapa 1: os três serviços da saga estão no ar."""
from verificador import executar, http, verificacao

SERVICOS = {"pedidos": 8031, "estoque": 8032, "pagamentos": 8033}

for nome, porta in SERVICOS.items():
    def checar(porta=porta):
        status, _ = http("GET", f"http://localhost:{porta}/saude")
        assert status == 200, f"/saude devolveu HTTP {status}."
    verificacao(f"{nome} responde em http://localhost:{porta}/saude")(checar)


executar(parar_na_primeira_falha=True)
