"""Barramento de eventos sobre Redis Streams, com grupos de consumidores.

Todos os eventos da saga vão para um único stream (``saga.eventos``). Cada
serviço participa como um *grupo de consumidores* e recebe todos os eventos,
uma vez cada. Depois de tratar um evento, o serviço o confirma (XACK).

Se o tratamento falhar (por exemplo, um tratador ainda não implementado), o
evento NÃO é confirmado: fica pendente e é reprocessado quando o serviço
reiniciar, o que acontece sozinho sempre que você salva o código. Assim,
nenhuma etapa da saga se perde.

Este arquivo é infraestrutura: você não precisa alterá-lo no tutorial.
"""
from __future__ import annotations

import json
import time
from typing import Callable

import redis

STREAM_SAGA = "saga.eventos"
CONSUMIDOR = "consumidor-1"


class Barramento:
    def __init__(self, url: str, servico: str, stream: str = STREAM_SAGA) -> None:
        self.servico = servico
        self.stream = stream
        self.redis = redis.Redis.from_url(url, decode_responses=True)

    def publicar(self, evento: dict, origem: str | None = None) -> str:
        return self.redis.xadd(self.stream, {
            "tipo": evento["tipo"],
            "origem": origem or self.servico,
            "dados": json.dumps(evento["dados"], ensure_ascii=False),
        })

    def historico(self, filtro: Callable[[dict], bool] = lambda _evento: True) -> list[dict]:
        """Todos os eventos já publicados (em ordem) que passam pelo filtro."""
        eventos = []
        for id_mensagem, campos in self.redis.xrange(self.stream):
            evento = self._decodificar(campos)
            if filtro(evento):
                eventos.append({"publicado_em_ms": int(id_mensagem.split("-")[0]), **evento})
        return eventos

    def consumir(self, ao_receber: Callable[[dict], None]) -> None:
        """Entrega cada evento do stream a ``ao_receber``. Nunca retorna."""
        self._aguardar_redis()
        try:
            self.redis.xgroup_create(self.stream, self.servico, id="0", mkstream=True)
        except redis.ResponseError as erro:
            if "BUSYGROUP" not in str(erro):  # o grupo já existe: tudo bem
                raise

        # 1) eventos pendentes: recebidos antes, mas não confirmados
        ultimo_pendente = "0"
        while True:
            resposta = self.redis.xreadgroup(self.servico, CONSUMIDOR, {self.stream: ultimo_pendente}, count=100)
            mensagens = resposta[0][1] if resposta else []
            if not mensagens:
                break
            for id_mensagem, campos in mensagens:
                self._processar(id_mensagem, campos, ao_receber, reprocessando=True)
                ultimo_pendente = id_mensagem

        # 2) eventos novos, para sempre
        while True:
            try:
                resposta = self.redis.xreadgroup(self.servico, CONSUMIDOR, {self.stream: ">"}, count=10, block=5000)
            except redis.ConnectionError:
                print(f"[{self.servico}] Redis indisponível, tentando de novo em 2s...")
                time.sleep(2)
                continue
            for _stream, mensagens in resposta or []:
                for id_mensagem, campos in mensagens:
                    self._processar(id_mensagem, campos, ao_receber)

    def _processar(self, id_mensagem: str, campos: dict, ao_receber, reprocessando: bool = False) -> None:
        if not campos:  # evento pendente que já foi apagado do stream
            self.redis.xack(self.stream, self.servico, id_mensagem)
            return
        evento = self._decodificar(campos)
        if reprocessando:
            print(f"[{self.servico}] reprocessando evento pendente: {evento['tipo']}")
        try:
            ao_receber(evento)
        except NotImplementedError as erro:
            print(f"[{self.servico}] ⚠ {evento['tipo']} NÃO tratado: {erro}. "
                  "O evento ficou PENDENTE e será reprocessado quando você salvar o código.")
            return
        except Exception as erro:  # noqa: BLE001 - não derruba o consumidor
            print(f"[{self.servico}] ⚠ erro ao tratar {evento['tipo']}: {type(erro).__name__}: {erro}. "
                  "O evento ficou PENDENTE e será reprocessado quando você salvar o código.")
            return
        self.redis.xack(self.stream, self.servico, id_mensagem)

    @staticmethod
    def _decodificar(campos: dict) -> dict:
        return {"tipo": campos["tipo"], "origem": campos.get("origem", "?"), "dados": json.loads(campos["dados"])}

    def _aguardar_redis(self) -> None:
        while True:
            try:
                self.redis.ping()
                return
            except redis.ConnectionError:
                time.sleep(1)
