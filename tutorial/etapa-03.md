# Etapa 3 — Quando a saga dá errado

**Objetivo:** fazer o serviço de pedidos reagir aos eventos de falha.

Uma saga tem **vários desfechos possíveis**. O serviço de pedidos já trata o
caminho feliz (`ao_pagamento_aprovado`). Faltam os dois caminhos de falha, em
`servicos/pedidos/pedidos.py`:

| Evento recebido | Novo status | `motivo` | Evento publicado |
| --- | --- | --- | --- |
| `EstoqueIndisponivel` | `CANCELADO` | `"estoque indisponível"` | `PedidoCancelado` |
| `PagamentoRecusado` | `CANCELADO` | `dados["motivo"]` | `PedidoCancelado` |

Siga o exemplo de `ao_pagamento_aprovado`. A função auxiliar `_pedido_pendente`
já cuida da idempotência: só deixa passar pedidos que ainda estão `PENDENTE`.

## Teste no serviço

```bash
docker compose restart pedidos && sleep 3
```

**Falta de estoque.** Há só 2 monitores; a `carla` pede 5:

```bash
curl -s -w '\n' -X POST localhost:8031/pedidos -H 'Content-Type: application/json' \
  -d '{"cliente": "carla", "produto": "monitor", "quantidade": 5}' | tee /tmp/pedido-carla.json
sleep 1
curl -s -w '\n' localhost:8031/pedidos/$(python3 -c 'import json; print(json.load(open("/tmp/pedido-carla.json"))["pedido_id"])')
```

**Saldo insuficiente.** O `bruno` tem R$ 100,00 e pede um monitor de R$ 900,00:

```bash
curl -s -w '\n' -X POST localhost:8031/pedidos -H 'Content-Type: application/json' \
  -d '{"cliente": "bruno", "produto": "monitor", "quantidade": 1}' | tee /tmp/pedido-bruno.json
sleep 1
PEDIDO_BRUNO=$(python3 -c 'import json; print(json.load(open("/tmp/pedido-bruno.json"))["pedido_id"])')
curl -s localhost:8031/pedidos/$PEDIDO_BRUNO/historico
curl -s -w '\n' localhost:8031/pedidos/$PEDIDO_BRUNO
```

O pedido do bruno foi `CANCELADO`. Agora olhe o estoque:

```bash
curl -s -w '\n' localhost:8032/estoque
```

Há um problema: **1 monitor continua reservado** para um pedido cancelado. O
estoque reservou o produto antes de o pagamento falhar, e ninguém desfez a
reserva. O sistema está **inconsistente**. A próxima etapa resolve isso.

Clique em **Verificar**. A verificação testa `pedidos.py` diretamente.
