"""Barramento de eventos sobre RabbitMQ.

Como as peças se encaixam:

    publicar ──▶ EXCHANGE "saga.eventos" ──(bindings)──▶ FILA de cada serviço ──▶ consumir

- O exchange é do tipo *topic*: a routing key de cada mensagem é o TIPO do
  evento (ex.: "EstoqueReservado").
- Cada serviço tem a SUA fila e assina só os tipos que sabe tratar: um
  binding para cada chave do dicionário TRATADORES.
- A fila "saga.historico" assina "#" (todos os eventos). É dela que sai a
  linha do tempo de /pedidos/<id>/historico.
- Filas e mensagens são duráveis: se um serviço estiver fora do ar, os
  eventos esperam na fila dele.
- Depois de tratar um evento, o serviço o confirma (ack). Se o tratamento
  falhar (por exemplo, um tratador ainda não implementado), o evento NÃO é
  confirmado: fica "Unacked" e volta para a fila quando o serviço reinicia,
  o que acontece sozinho sempre que você salva o código.

Este arquivo é infraestrutura: você não precisa alterá-lo no tutorial.
"""
from __future__ import annotations

import json
import time
from typing import Callable

import pika
from pika.exceptions import AMQPError

EXCHANGE = "saga.eventos"
FILA_HISTORICO = "saga.historico"


class Barramento:
    def __init__(self, url: str, servico: str) -> None:
        self.url = url
        self.servico = servico

    # --- publicar -------------------------------------------------------------
    def publicar(self, evento: dict, origem: str | None = None) -> None:
        """Publica um evento usando uma conexão curta (fora do consumidor)."""
        conexao = self._conectar()
        try:
            canal = conexao.channel()
            canal.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)
            self._publicar_no_canal(canal, evento, origem)
        finally:
            conexao.close()

    def _publicar_no_canal(self, canal, evento: dict, origem: str | None = None) -> None:
        canal.basic_publish(
            exchange=EXCHANGE,
            routing_key=evento["tipo"],
            body=json.dumps(evento["dados"], ensure_ascii=False).encode(),
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=pika.DeliveryMode.Persistent,  # sobrevive a um restart do RabbitMQ
                type=evento["tipo"],
                app_id=origem or self.servico,
                headers={"publicado_em_ms": int(time.time() * 1000)},
            ),
        )

    # --- consumir -------------------------------------------------------------
    def consumir(self, fila: str, assinaturas: list[str], ao_receber: Callable[[dict], list],
                 ao_ficar_pronto: Callable[[], None] = lambda: None) -> None:
        """Cria a fila, assina os tipos de evento e entrega cada evento a
        ``ao_receber``, que devolve a lista de eventos a publicar. Nunca retorna."""
        while True:
            conexao = self._conectar()
            try:
                canal = conexao.channel()
                canal.exchange_declare(EXCHANGE, exchange_type="topic", durable=True)
                canal.queue_declare(fila, durable=True)
                for routing_key in assinaturas:
                    canal.queue_bind(fila, EXCHANGE, routing_key=routing_key)
                canal.basic_qos(prefetch_count=50)  # um evento travado não impede os seguintes

                def ao_chegar(canal, entrega, propriedades, corpo):
                    self._processar(canal, entrega, propriedades, corpo, ao_receber)

                canal.basic_consume(fila, on_message_callback=ao_chegar)
                ao_ficar_pronto()
                canal.start_consuming()
            except AMQPError as erro:
                print(f"[{self.servico}] conexão com o RabbitMQ caiu ({type(erro).__name__}); reconectando...")
                time.sleep(2)

    def _processar(self, canal, entrega, propriedades, corpo: bytes, ao_receber) -> None:
        evento = {
            "tipo": propriedades.type or entrega.routing_key,
            "origem": propriedades.app_id or "?",
            "publicado_em_ms": (propriedades.headers or {}).get("publicado_em_ms", int(time.time() * 1000)),
            "dados": json.loads(corpo),
        }
        if entrega.redelivered:
            print(f"[{self.servico}] reprocessando evento pendente: {evento['tipo']}")
        try:
            novos_eventos = ao_receber(evento)
        except NotImplementedError as erro:
            print(f"[{self.servico}] ⚠ {evento['tipo']} NÃO tratado: {erro}. "
                  "O evento ficou PENDENTE (Unacked) e volta para a fila quando você salvar o código.")
            return
        except Exception as erro:  # noqa: BLE001 - não derruba o consumidor
            print(f"[{self.servico}] ⚠ erro ao tratar {evento['tipo']}: {type(erro).__name__}: {erro}. "
                  "O evento ficou PENDENTE (Unacked) e volta para a fila quando você salvar o código.")
            return
        for novo in novos_eventos:
            self._publicar_no_canal(canal, novo)
            print(f"[{self.servico}]   → publicou {novo['tipo']} (pedido {novo['dados'].get('pedido_id')})")
        canal.basic_ack(entrega.delivery_tag)  # confirma: o RabbitMQ pode apagar a mensagem

    def _conectar(self) -> pika.BlockingConnection:
        while True:
            try:
                return pika.BlockingConnection(pika.URLParameters(self.url))
            except AMQPError:
                print(f"[{self.servico}] RabbitMQ indisponível, tentando de novo em 2s...")
                time.sleep(2)
