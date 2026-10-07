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

from flask import Flask, jsonify

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
        self.app.json.compact = False  # respostas indentadas: mais fáceis de ler no terminal
        self.app.get("/saude")(lambda: {"servico": nome, "status": "ok"})
        self.app.post("/simular/reentrega/<pedido_id>")(self._simular_reentrega)
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
            # Transação LOCAL: o tratador trabalha numa cópia do estado. Só se ele
            # terminar sem erro a cópia vira o estado oficial e é gravada no banco.
            rascunho = copy.deepcopy(self.estado)
            novos_eventos = tratador(rascunho, evento["dados"])
            if novos_eventos is None:
                # Um tratador completo sempre termina com `return [...]`.
                raise NotImplementedError(f"{tratador.__name__} ainda não devolve nada (falta escrever o código)")
            self.estado.clear()
            self.estado.update(rascunho)
            self.salvar()
        self.publicar(novos_eventos)

    def _simular_reentrega(self, pedido_id: str):
        """Publica de novo o último evento deste pedido que o serviço trata, como
        faria um produtor que reenviou a mensagem (entrega "pelo menos uma vez")."""
        eventos = self.barramento.historico(
            lambda e: e["tipo"] in self.tratadores and e["dados"].get("pedido_id") == pedido_id
        )
        if not eventos:
            return jsonify(erro=f"Nenhum evento tratado por '{self.nome}' para o pedido '{pedido_id}'."), 404
        repetido = eventos[-1]
        self.barramento.publicar(repetido, origem=repetido["origem"])
        print(f"[{self.nome}] ⟳ simulação: {repetido['tipo']} (pedido {pedido_id}) foi entregue DE NOVO")
        return jsonify(reentregue=repetido["tipo"], pedido_id=pedido_id), 202

    def iniciar(self) -> None:
        # use_reloader: ao salvar um .py, o serviço reinicia sozinho com o código
        # novo e reprocessa os eventos que ficaram pendentes. O consumidor só roda
        # no processo filho (o que atende as requisições), não no que vigia os arquivos.
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            threading.Thread(target=self.barramento.consumir, args=(self._ao_receber,), daemon=True).start()
            print(f"[{self.nome}] pronto; reage a: {', '.join(self.tratadores) or '(nada)'}")
        self.app.run(host="0.0.0.0", port=8000, threaded=True, use_reloader=True)
