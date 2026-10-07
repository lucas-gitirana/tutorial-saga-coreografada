![Mapa: desfechos de falha](tutorial/img/mapa-falhas.svg)

📍 **Você está aqui:** no `pedidos`, que recebe o **desfecho** de cada saga.

## Os desfechos que o `pedidos` precisa tratar

| Evento recebido | Novo `status` | `motivo` | Publica | Etapa |
| --- | --- | --- | --- | --- |
| `PagamentoAprovado` | `CONFIRMADO` | — | `PedidoConfirmado` | pronto |
| `EstoqueIndisponivel` | `CANCELADO` | `"estoque indisponível"` | `PedidoCancelado` | **esta** |
| `PagamentoRecusado` | `CANCELADO` | o que veio no evento | `PedidoCancelado` | 8 |

## 🧪 Primeiro, provoque a falha

O estoque tem no máximo 2 monitores, e a `carla` pede **5**:

**`POST http://localhost:8031/pedidos`**

```json
{ "cliente": "carla", "produto": "monitor", "quantidade": 5 }
```

```bash
curl -s -X POST localhost:8031/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente": "carla", "produto": "monitor", "quantidade": 5}' \
  -w '← HTTP %{http_code}\n'
```

```bash
curl -s localhost:8031/pedidos/carla-1/historico
```

O estoque publicou `EstoqueIndisponivel`, mas o pedido segue `PENDENTE`: o
evento está pendente no `pedidos`.

## ✏️ Faça

`_pedido_pendente` (já pronta) devolve o pedido **só se ele ainda estiver
`PENDENTE`**. Se ele não existe ou já teve desfecho, devolve `None`.

Abaixo do marcador **Etapa 7**, escreva o código, seguindo o exemplo
`ao_pagamento_aprovado` logo acima no arquivo. Complete o `___`:

```python
    if pedido is None:
        return []    # pedido desconhecido ou que já teve desfecho
    pedido["status"] = ___
    pedido["motivo"] = "estoque indisponível"
    return [evento("PedidoCancelado", pedido_id=pedido["pedido_id"], motivo=pedido["motivo"])]
```

**Salve** (`Ctrl+S`).

## 🧪 Teste

Ao salvar, o `pedidos` reprocessa o evento pendente da `carla`:

```bash
curl -s localhost:8031/pedidos/carla-1
```

Agora o pedido está `CANCELADO`, com o motivo `"estoque indisponível"`.
Repare: o `pagamentos` **nem ficou sabendo** desse pedido, e a `carla` não foi
cobrada. A saga terminou antes de chegar nele.

## Clique em Verificar ✔
