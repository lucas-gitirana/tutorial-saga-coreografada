![Mapa: visão geral](tutorial/img/mapa-geral.svg)

📍 **Você está aqui:** o mapa inteiro funcionando. E se uma peça cair no meio
da saga?

## 1. Derrube o `pagamentos`

```bash
docker compose stop pagamentos
```

## 2. Faça um pedido mesmo assim

**`POST http://localhost:8031/pedidos`**

```json
{ "cliente": "carla", "produto": "teclado", "quantidade": 1 }
```

```bash
curl -s -X POST localhost:8031/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente": "carla", "produto": "teclado", "quantidade": 1}' \
  -w '← HTTP %{http_code}\n'
```

A resposta veio normalmente (`202`), com o `pedido_id` **`carla-2`**. O pedido
fica `PENDENTE`, mas **nada quebrou**: o `pedidos` e o `estoque` fizeram a sua
parte e continuam respondendo. E o `EstoqueReservado`?

```bash
docker compose exec rabbitmq rabbitmqctl -q list_queues name messages_ready messages_unacknowledged | column -t
```

Ele está **esperando na fila** `pagamentos` (`messages_ready` = 1). A fila
existe mesmo com o serviço desligado.

## 3. Suba o `pagamentos` de novo

```bash
docker compose up -d --wait pagamentos
sleep 2
curl -s localhost:8031/pedidos/carla-2
```

O pedido está `CONFIRMADO`. O `EstoqueReservado` **esperou na fila** até o
`pagamentos` voltar, e a saga terminou sozinha.

| Com chamadas HTTP diretas | Com eventos (saga coreografada) |
| --- | --- |
| `pedidos → estoque → pagamentos`: se o `pagamentos` está fora, o pedido **falha na hora** | o evento espera; quando o `pagamentos` volta, a saga **continua** |

Isso é **desacoplamento temporal**: os serviços não precisam estar no ar ao
mesmo tempo.

## 4. Todos os desfechos

```bash
curl -s localhost:8031/pedidos/resumo
```

Lá estão os caminhos da saga que você construiu: `CONFIRMADO` (ana, carla-2)
e `CANCELADO` por falta de estoque (carla-1) e por falta de saldo (bruno-1).

## 5. Clique em Verificar ✔

A verificação roda os três desfechos de ponta a ponta, com clientes novos, e
confere o estoque, os saldos e a linha do tempo da saga compensada.
