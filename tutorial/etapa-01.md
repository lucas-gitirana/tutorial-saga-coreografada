# Etapa 1 — Iniciando uma saga

**Objetivo:** criar um pedido e acompanhar os eventos da saga.

## 1. Confira os serviços

```bash
docker compose ps
```

São quatro containers: `redis`, `pedidos`, `estoque` e `pagamentos`. Cada
serviço tem **o seu próprio volume de dados**. Ninguém lê o banco do outro.

## 2. Faça um pedido

A cliente `ana` tem R$ 1000,00 na carteira. Ela vai comprar 2 teclados
(R$ 150,00 cada):

```bash
curl -s -w '\n' -X POST localhost:8031/pedidos -H 'Content-Type: application/json' \
  -d '{"cliente": "ana", "produto": "teclado", "quantidade": 2}' | tee /tmp/pedido-ana.json
```

A resposta é **HTTP 202 Accepted**, com status `PENDENTE`. O pedido foi
aceito, mas o desfecho depende dos outros serviços.

## 3. Acompanhe a saga

Guarde o id e veja a **linha do tempo** dos eventos desse pedido:

```bash
PEDIDO_ANA=$(python3 -c 'import json; print(json.load(open("/tmp/pedido-ana.json"))["pedido_id"])')
curl -s localhost:8031/pedidos/$PEDIDO_ANA/historico
curl -s -w '\n' localhost:8031/pedidos/$PEDIDO_ANA
```

O estoque reagiu ao `PedidoCriado` e publicou `EstoqueReservado`... e a saga
parou. O pedido continua `PENDENTE`.

## 4. Descubra por quê

```bash
docker compose logs pagamentos
```

O serviço de pagamentos recebeu o `EstoqueReservado`, mas não sabe tratá-lo
(é a sua tarefa da Etapa 2). Repare na mensagem: o evento **ficou pendente**
no Redis e será reprocessado quando o serviço reiniciar. Ele não se perdeu.

Veja também que o estoque já está reservado:

```bash
curl -s -w '\n' localhost:8032/estoque
```

Clique em **Verificar** para concluir a etapa.
