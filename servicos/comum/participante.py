"""Esqueleto comum dos três serviços participantes da saga.

Cada serviço tem o SEU banco de dados (aqui, um arquivo JSON em um volume
Docker próprio) e um dicionário TRATADORES que diz a quais eventos ele reage:

    TRATADORES = {"EstoqueReservado": ao_estoque_reservado, ...}

As chaves de TRATADORES viram as ASSINATURAS (bindings) da fila do serviço no
RabbitMQ: ele só recebe os tipos de evento que sabe tratar.

Um tratador recebe (estado, dados_do_evento), altera o estado do serviço e
devolve a lista de eventos a publicar. Ele não sabe nada de RabbitMQ ou HTTP,
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

from barramento import FILA_HISTORICO, Barramento


class Participante:
    def __init__(self, nome: str, estado_inicial: dict, tratadores: dict[str, Callable],
                 guardar_historico: bool = False) -> None:
        self.nome = nome
        self.tratadores = tratadores
        self.guardar_historico = guardar_historico
        self.trava = threading.Lock()
        self.barramento = Barramento(os.environ.get("AMQP_URL", "amqp://guest:guest@localhost:5672/%2F"), nome)
        self._arquivo = os.environ.get("ARQUIVO_ESTADO", f"{nome}.json")
        pasta = os.path.dirname(self._arquivo) or "."
        self._arquivo_recebidos = os.path.join(pasta, "eventos-recebidos.jsonl")
        self._arquivo_historico = os.path.join(pasta, "historico-da-saga.jsonl")
        self.estado = self._carregar(estado_inicial)
        self._filas_prontas = 0

        self.app = Flask(nome)
        self.app.json.ensure_ascii = False
        self.app.json.sort_keys = False
        self.app.json.compact = False  # respostas indentadas: mais fáceis de ler no terminal
        self.app.get("/saude")(self._saude)
        self.app.post("/simular/reentrega/<pedido_id>")(self._simular_reentrega)
        logging.getLogger("werkzeug").setLevel(logging.WARNING)  # logs mostram só a saga
        logging.getLogger("pika").setLevel(logging.CRITICAL)

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

    def _ao_receber(self, evento: dict) -> list:
        tratador = self.tratadores[evento["tipo"]]  # a fila só recebe os tipos assinados
        print(f"[{self.nome}] ← recebeu {evento['tipo']} (pedido {evento['dados'].get('pedido_id')})")
        _anexar(self._arquivo_recebidos, evento)
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
        return novos_eventos

    def _registrar_no_historico(self, evento: dict) -> list:
        _anexar(self._arquivo_historico, evento)
        return []

    def historico(self, pedido_id: str) -> list[dict]:
        """Todos os eventos da saga deste pedido, em ordem (só no serviço pedidos)."""
        return [e for e in _ler(self._arquivo_historico) if e["dados"].get("pedido_id") == pedido_id]

    def _simular_reentrega(self, pedido_id: str):
        """Publica de novo o último evento deste pedido que o serviço recebeu, como
        faria um produtor que reenviou a mensagem (entrega "pelo menos uma vez")."""
        recebidos = [e for e in _ler(self._arquivo_recebidos) if e["dados"].get("pedido_id") == pedido_id]
        if not recebidos:
            return jsonify(erro=f"'{self.nome}' ainda não recebeu nenhum evento do pedido '{pedido_id}'."), 404
        repetido = recebidos[-1]
        self.barramento.publicar(repetido, origem=repetido["origem"])
        print(f"[{self.nome}] ⟳ simulação: {repetido['tipo']} (pedido {pedido_id}) foi entregue DE NOVO")
        return jsonify(reentregue=repetido["tipo"], pedido_id=pedido_id), 202

    # --- ciclo de vida ----------------------------------------------------------
    def _saude(self):
        esperadas = 2 if self.guardar_historico else 1
        if self._filas_prontas < esperadas:
            return jsonify(servico=self.nome, status="conectando ao RabbitMQ"), 503
        return jsonify(servico=self.nome, status="ok")

    def _fila_pronta(self) -> None:
        self._filas_prontas += 1

    def _consumir_em_segundo_plano(self, fila: str, assinaturas: list[str], ao_receber) -> None:
        threading.Thread(target=self.barramento.consumir, daemon=True,
                         args=(fila, assinaturas, ao_receber, self._fila_pronta)).start()

    def iniciar(self) -> None:
        # use_reloader: ao salvar um .py, o serviço reinicia sozinho com o código
        # novo. A conexão antiga com o RabbitMQ cai, os eventos não confirmados
        # voltam para a fila e são entregues de novo. Os consumidores só rodam no
        # processo filho (o que atende as requisições), não no que vigia os arquivos.
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self._consumir_em_segundo_plano(self.nome, list(self.tratadores), self._ao_receber)
            if self.guardar_historico:
                self._consumir_em_segundo_plano(FILA_HISTORICO, ["#"], self._registrar_no_historico)
            print(f"[{self.nome}] pronto; a fila '{self.nome}' assina: {', '.join(self.tratadores) or '(nada)'}")
        self.app.run(host="0.0.0.0", port=8000, threaded=True, use_reloader=True)


def _anexar(arquivo: str, evento: dict) -> None:
    with open(arquivo, "a", encoding="utf-8") as saida:
        saida.write(json.dumps(evento, ensure_ascii=False) + "\n")


def _ler(arquivo: str) -> list[dict]:
    if not os.path.exists(arquivo):
        return []
    eventos = []
    with open(arquivo, encoding="utf-8") as entrada:
        for linha in entrada:
            try:
                eventos.append(json.loads(linha))
            except ValueError:  # linha sendo escrita neste instante
                pass
    return eventos
