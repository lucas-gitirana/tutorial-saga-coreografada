"""Esqueleto comum dos três serviços participantes da saga.

Cada serviço tem o SEU banco de dados (aqui, um arquivo JSON em um volume
Docker próprio) e um dicionário TRATADORES que diz a quais eventos ele reage:

    TRATADORES = {"EstoqueReservado": ao_estoque_reservado, ...}

Um tratador recebe (estado, dados_do_evento), altera o estado do serviço e
devolve a lista de eventos a publicar. Ele não sabe nada de Redis ou HTTP,
por isso pode ser testado sem subir nenhum container.

Este arquivo é infraestrutura: você não precisa alterá-lo no tutorial.
"""
from __future__ import annotations

import copy
import json
import logging
import os
import threading
from typing import Callable

from flask import Flask

from barramento import Barramento


class Participante:
    def __init__(self, nome: str, estado_inicial: dict, tratadores: dict[str, Callable]) -> None:
        self.nome = nome
        self.tratadores = tratadores
        self.trava = threading.Lock()
        self.barramento = Barramento(os.environ.get("REDIS_URL", "redis://localhost:6379/0"), nome)
        self._arquivo = os.environ.get("ARQUIVO_ESTADO", f"{nome}.json")
        self.estado = self._carregar(estado_inicial)

        self.app = Flask(nome)
        self.app.json.ensure_ascii = False
        self.app.json.sort_keys = False
        self.app.get("/saude")(lambda: {"servico": nome, "status": "ok"})
        logging.getLogger("werkzeug").setLevel(logging.WARNING)  # logs mostram só a saga

    # --- banco de dados do serviço -----------------------------------------
    def _carregar(self, estado_inicial: dict) -> dict:
        if os.path.exists(self._arquivo):
            with open(self._arquivo, encoding="utf-8") as arquivo:
                return json.load(arquivo)
        return copy.deepcopy(estado_inicial)

    def salvar(self) -> None:
        temporario = f"{self._arquivo}.tmp"
        with open(temporario, "w", encoding="utf-8") as arquivo:
            json.dump(self.estado, arquivo, ensure_ascii=False, indent=2)
        os.replace(temporario, self._arquivo)

    # --- eventos ------------------------------------------------------------
    def publicar(self, eventos: list[dict]) -> None:
        for evento in eventos:
            self.barramento.publicar(evento)
            print(f"[{self.nome}]   → publicou {evento['tipo']} (pedido {evento['dados'].get('pedido_id')})")

    def _ao_receber(self, evento: dict) -> None:
        tratador = self.tratadores.get(evento["tipo"])
        if tratador is None:
            return  # evento que não interessa a este serviço
        print(f"[{self.nome}] ← recebeu {evento['tipo']} (pedido {evento['dados'].get('pedido_id')})")
        with self.trava:
            novos_eventos = tratador(self.estado, evento["dados"]) or []
            self.salvar()
        self.publicar(novos_eventos)

    def iniciar(self) -> None:
        threading.Thread(target=self.barramento.consumir, args=(self._ao_receber,), daemon=True).start()
        print(f"[{self.nome}] pronto; reage a: {', '.join(self.tratadores) or '(nada)'}")
        self.app.run(host="0.0.0.0", port=8000, threaded=True)

