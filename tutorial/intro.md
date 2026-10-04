# Padrão Saga Coreografada na prática

**Tempo estimado:** 40 minutos · **Linguagem:** Python (Flask) · **Infra:** Docker Compose + Redis

## O problema: transações que cruzam serviços

Em microsserviços, **cada serviço tem o seu próprio banco de dados**. Uma
operação de negócio como "fazer um pedido" precisa mexer em três deles:

- **pedidos**: registrar o pedido;
- **estoque**: reservar o produto;
- **pagamentos**: cobrar o cliente.

Não existe uma transação ACID que abranja três bancos diferentes. Se o
pagamento falhar depois de o estoque ser reservado, quem desfaz a reserva?

## A ideia da Saga

Uma **saga** é uma sequência de **transações locais**, uma em cada serviço.
Cada etapa faz a sua parte, grava no seu banco e publica um evento que dispara
a próxima. Se uma etapa falha, as anteriores são desfeitas por **transações de
compensação**. O sistema não volta exatamente ao estado inicial, mas fica
**consistente** com ele (Nadareishvili *et al.*, 2016).

Na saga **coreografada** não existe um coordenador central. Cada serviço
**escuta os eventos dos outros e reage** (Richardson, 2018). Dois princípios
guiam a implementação:

1. cada participante **atualiza o seu banco e publica um evento**;
2. cada participante usa um **id de correlação** (aqui, o `pedido_id`) para
   ligar os eventos que recebe aos seus próprios dados.

## O cenário

```text
                      ┌──────────────────────── Redis Stream: saga.eventos ────────────────────────┐
                      │                                                                             │
 POST /pedidos ─▶ [pedidos] ──PedidoCriado──▶ [estoque] ──EstoqueReservado──▶ [pagamentos]         │
   (8031)             ▲          (8032)          │                                  │   (8033)      │
                      │                          │ EstoqueIndisponivel              │               │
                      │◀─────────────────────────┘                                  │               │
                      │◀──────────────────────── PagamentoAprovado ─────────────────┤               │
                      │◀──────────────────────── PagamentoRecusado ─────────────────┘               │
                      │                              │                                              │
                      │                              ▼                                              │
                      │                          [estoque] ── COMPENSAÇÃO: libera a reserva         │
                      └─────────────────────────────────────────────────────────────────────────────┘
```

| Evento | Publicado por | Quem reage |
| --- | --- | --- |
| `PedidoCriado` | pedidos | estoque: tenta reservar |
| `EstoqueReservado` | estoque | pagamentos: tenta cobrar |
| `EstoqueIndisponivel` | estoque | pedidos: cancela |
| `PagamentoAprovado` | pagamentos | pedidos: confirma |
| `PagamentoRecusado` | pagamentos | pedidos: cancela · estoque: **compensa** |

## O que você vai fazer

1. Iniciar uma saga e ver que ela **trava** sem o participante de pagamentos.
2. Implementar o participante **pagamentos**.
3. Tratar os **desfechos de falha** no serviço de pedidos.
4. Implementar a **transação de compensação** do estoque.
5. Rodar a saga completa e testar a resiliência a um serviço fora do ar.

## Como funciona este tutorial

- Blocos de comando têm um botão **▶ Executar**, que roda o comando no terminal integrado.
- Etapas com avaliação têm o botão **Verificar**. Se algo falhar, leia a saída:
  ela diz o que está faltando.
- Os arquivos que você vai editar abrem sozinhos, na linha do `TODO`.

## Preparando o ambiente

Ao abrir esta introdução, o terminal já começou a subir os containers. Se
precisar rodar de novo:

```bash
docker compose up -d --build --wait
```

> Pré-requisitos: Docker com Docker Compose e Python 3 (usado pelas
> verificações). No GitHub Codespaces, tudo já vem instalado.
