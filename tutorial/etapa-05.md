# Etapa 5 — A saga completa

**Objetivo:** ver todos os caminhos da saga funcionando e testar a resiliência
da comunicação assíncrona.

## 1. Os três desfechos

```bash
for pedido in '{"cliente": "carla", "produto": "mouse", "quantidade": 3}' \
              '{"cliente": "bruno", "produto": "teclado", "quantidade": 1}' \
              '{"cliente": "carla", "produto": "monitor", "quantidade": 10}'; do
  curl -s -X POST localhost:8031/pedidos -H 'Content-Type: application/json' -d "$pedido" > /dev/null
done
sleep 1
curl -s localhost:8031/pedidos | python3 -c '
import sys, json
for p in json.load(sys.stdin):
    print(p["pedido_id"], p["cliente"].ljust(6), p["produto"].ljust(8), p["status"].ljust(11), p["motivo"] or "")'
```

## 2. Um serviço fora do ar

O que acontece se o serviço de pagamentos cair no meio da saga?

```bash
docker compose stop pagamentos
curl -s -w '\n' -X POST localhost:8031/pedidos -H 'Content-Type: application/json' \
  -d '{"cliente": "carla", "produto": "teclado", "quantidade": 1}' | tee /tmp/pedido-resiliencia.json
sleep 2
curl -s -w '\n' localhost:8031/pedidos/$(python3 -c 'import json; print(json.load(open("/tmp/pedido-resiliencia.json"))["pedido_id"])')
```

O pedido fica `PENDENTE`, mas **nada quebra**: o pedidos e o estoque fizeram
a sua parte e seguem respondendo. Agora suba o pagamentos de novo:

```bash
docker compose start pagamentos && sleep 3
curl -s -w '\n' localhost:8031/pedidos/$(python3 -c 'import json; print(json.load(open("/tmp/pedido-resiliencia.json"))["pedido_id"])')
```

O evento esperou no Redis e a saga terminou sozinha (`CONFIRMADO`). Esse
**desacoplamento temporal** é uma vantagem da comunicação por eventos. Numa
cadeia de chamadas HTTP síncronas, o pedido teria falhado na hora.

## 3. Os logs de cada participante

```bash
docker compose logs --no-log-prefix estoque | tail -8
```

Clique em **Verificar**. A verificação roda os três desfechos de ponta a ponta
com clientes novos e confere estoque, saldos e a linha do tempo da saga.
