"""Gera os diagramas "você está aqui" (mapa-*.svg) usados no texto das etapas.

Cada mapa é o mesmo desenho da saga com uma parte destacada.
Para regenerar depois de mudar algo:  python3 tutorial/img/gerar_mapas.py
"""
from pathlib import Path

PEDIDOS, ESTOQUE, PAGAMENTOS, FALHA = "#1971c2", "#d9480f", "#2f9e44", "#c92a2a"
VOCE, APAGADO = "#495057", "#adb5bd"
FUNDO = {PEDIDOS: "#e7f5ff", ESTOQUE: "#fff4e6", PAGAMENTOS: "#ebfbee", VOCE: "#f1f3f5"}

# nome: (x, y, largura, altura, linha 1, linha 2, cor quando destacado)
CAIXAS = {
    "voce": (15, 123, 90, 54, "Você", "(curl)", VOCE),
    "pedidos": (160, 115, 160, 70, "pedidos", "porta 8031", PEDIDOS),
    "estoque": (480, 115, 160, 70, "estoque", "porta 8032", ESTOQUE),
    "pagamentos": (800, 115, 160, 70, "pagamentos", "porta 8033", PAGAMENTOS),
    "db_pedidos": (165, 245, 150, 50, "pedidos.json", "banco próprio", PEDIDOS),
    "db_estoque": (485, 245, 150, 50, "estoque.json", "banco próprio", ESTOQUE),
    "db_pagamentos": (805, 245, 150, 50, "pagamentos.json", "banco próprio", PAGAMENTOS),
}

# nome: (pontos da linha, rótulo, posição do rótulo, cor quando destacada)
SETAS = {
    "post": ([(107, 150), (158, 150)], "POST", (132, 140), VOCE),
    "criado": ([(322, 135), (478, 135)], "PedidoCriado", (400, 125), PEDIDOS),
    "reservado": ([(642, 135), (798, 135)], "EstoqueReservado", (720, 125), ESTOQUE),
    "indisponivel": ([(478, 167), (322, 167)], "EstoqueIndisponivel", (400, 183), FALHA),
    "compensa": ([(798, 167), (642, 167)], "PagamentoRecusado", (720, 183), FALHA),
    "desfecho": ([(880, 113), (880, 72), (240, 72), (240, 113)],
                 "PagamentoAprovado  ou  PagamentoRecusado", (560, 64), PAGAMENTOS),
    "grava_pedidos": ([(240, 187), (240, 243)], "grava", (248, 219), PEDIDOS),
    "grava_estoque": ([(560, 187), (560, 243)], "grava", (568, 219), ESTOQUE),
    "grava_pagamentos": ([(880, 187), (880, 243)], "grava", (888, 219), PAGAMENTOS),
}

TUDO = set(CAIXAS) | set(SETAS)
MAPAS = {
    "mapa-geral": TUDO,
    "mapa-inicio": {"voce", "post", "pedidos", "db_pedidos", "grava_pedidos", "criado",
                    "estoque", "db_estoque", "grava_estoque", "reservado"},
    "mapa-pagamentos": {"reservado", "pagamentos", "db_pagamentos", "grava_pagamentos", "desfecho"},
    "mapa-falhas": {"pedidos", "db_pedidos", "grava_pedidos", "indisponivel", "desfecho"},
    "mapa-compensacao": {"compensa", "estoque", "db_estoque", "grava_estoque"},
}


def _recuar(origem, destino, distancia):
    """Ponto a `distancia` px antes do destino (a linha termina na base da ponta)."""
    (x1, y1), (x2, y2) = origem, destino
    dx, dy = x2 - x1, y2 - y1
    tamanho = (dx * dx + dy * dy) ** 0.5
    return round(x2 - dx / tamanho * distancia, 1), round(y2 - dy / tamanho * distancia, 1)


def _ponta(origem, destino, cor, escala):
    """Triângulo da ponta da seta, apontando de `origem` para `destino`."""
    (x1, y1), (x2, y2) = origem, destino
    dx, dy = x2 - x1, y2 - y1
    tamanho = (dx * dx + dy * dy) ** 0.5
    ux, uy = dx / tamanho, dy / tamanho
    comprimento, largura = 11 * escala, 6 * escala
    bx, by = x2 - ux * comprimento, y2 - uy * comprimento
    vertices = [(x2, y2), (bx - uy * largura, by + ux * largura), (bx + uy * largura, by - ux * largura)]
    return f'<polygon points="{" ".join(f"{round(x, 1)},{round(y, 1)}" for x, y in vertices)}" fill="{cor}"/>'


def svg(destaque: set[str]) -> str:
    partes = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1030 310" width="100%" '
        'font-family="Segoe UI, Helvetica, Arial, sans-serif">',
    ]
    partes.append('<rect x="1" y="1" width="1028" height="308" rx="10" fill="#ffffff" stroke="#dee2e6"/>')
    partes.append('<text x="515" y="26" text-anchor="middle" font-size="13" fill="#868e96">'
                  'Cada seta é um evento no Redis (stream saga.eventos). Nenhum serviço chama o outro.</text>')

    for nome, (pontos, rotulo, (tx, ty), cor) in SETAS.items():
        ligado = nome in destaque
        c = cor if ligado else APAGADO
        caminho = " ".join(f"{x},{y}" for x, y in pontos[:-1] + [_recuar(pontos[-2], pontos[-1], 8)])
        partes.append(
            f'<polyline points="{caminho}" fill="none" stroke="{c}" stroke-width="{3 if ligado else 2}" '
            f'stroke-linejoin="round"/>'
        )
        partes.append(_ponta(pontos[-2], pontos[-1], c, 1.2 if ligado else 1.0))
        vertical = pontos[0][0] == pontos[-1][0] and len(pontos) == 2
        partes.append(f'<text x="{tx}" y="{ty}" text-anchor="{"start" if vertical else "middle"}" font-size="12" '
                      f'fill="{c}" font-weight="{600 if ligado else 400}">{rotulo}</text>')

    for nome, (x, y, w, h, l1, l2, cor) in CAIXAS.items():
        ligado = nome in destaque
        c = cor if ligado else APAGADO
        fundo = FUNDO[cor] if ligado else "#ffffff"
        tracejado = ' stroke-dasharray="5 3"' if nome.startswith("db_") else ""
        partes.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fundo}" stroke="{c}" '
                      f'stroke-width="{2.5 if ligado else 1.5}"{tracejado}/>')
        cx = x + w / 2
        partes.append(f'<text x="{cx}" y="{y + h / 2 - 3}" text-anchor="middle" font-size="14" font-weight="700" '
                      f'fill="{c}">{l1}</text>')
        partes.append(f'<text x="{cx}" y="{y + h / 2 + 14}" text-anchor="middle" font-size="12" '
                      f'fill="{"#495057" if ligado else APAGADO}">{l2}</text>')

    partes.append('</svg>')
    return "\n".join(partes) + "\n"


if __name__ == "__main__":
    pasta = Path(__file__).parent
    for nome, destaque in MAPAS.items():
        (pasta / f"{nome}.svg").write_text(svg(destaque), encoding="utf-8")
        print(f"gerado {nome}.svg")
