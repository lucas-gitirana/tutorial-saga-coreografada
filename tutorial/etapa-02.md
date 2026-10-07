![Mapa: início da saga](tutorial/img/mapa-inicio.svg)

📍 **Você está aqui:** começando uma saga. Você faz o pedido; o `pedidos` e o
`estoque` reagem.

## 1. A requisição

A cliente `ana` tem R$ 1000 e quer **2 teclados** (R$ 150 cada):

**`POST http://localhost:8031/pedidos`**

```json
{ "cliente": "ana", "produto": "teclado", "quantidade": 2 }
```

## 2. Envie

```bash
curl -s -X POST localhost:8031/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente": "ana", "produto": "teclado", "quantidade": 2}' \
  -w '← HTTP %{http_code}\n'
```

## 3. Olhe a resposta

```text
{
  "pedido_id": "ana-1",
  "cliente": "ana",
  "produto": "teclado",
  "quantidade": 2,
  "valor_total": 300.0,
  "status": "PENDENTE",
  "motivo": null
}
← HTTP 202
```

| Repare em | O que significa |
| --- | --- |
| **202 Accepted** | "recebi, mas ainda não terminei". Não é 201 (Created) porque o resultado depende de **outros serviços** |
| `"status": "PENDENTE"` | o pedido está esperando o resto da saga |
| `"pedido_id": "ana-1"` | o **id de correlação**: todo evento desta saga vai carregar esse id. É com ele que cada serviço sabe de qual pedido o evento fala |

## 4. Clique em Verificar ✔
