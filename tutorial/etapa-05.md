![Mapa: pagamentos](tutorial/img/mapa-pagamentos.svg)

📍 **Você está aqui:** no mesmo tratador do `pagamentos`. Agora, o caso em que
o saldo **não dá**.

## O que deve acontecer

| Situação | No banco do `pagamentos` | Evento publicado |
| --- | --- | --- |
| saldo **suficiente** | debita e registra `APROVADO` *(Etapa 4)* | `PagamentoAprovado` |
| saldo **insuficiente** | registra `RECUSADO`; o saldo **não muda** | `PagamentoRecusado`, com um `motivo` |

## 🐍 Python rápido: `return` antecipado

`return` termina a função **na hora**. Por isso o `if` da recusa fica **acima**
do código da Etapa 4: quem não tem saldo sai da função antes de ser cobrado.

```python
if saldo < valor:
    ...
    return [...]      # sem saldo: a função termina aqui
# só chega aqui quem tem saldo
```

## ✏️ Faça

Abaixo do marcador **Etapa 5** (acima do que você escreveu na Etapa 4),
escreva o `if` e complete os `___`:

```python
    if saldo < valor:
        estado["pagamentos"][pedido_id] = {"cliente": cliente, "valor": valor, "status": ___}
        return [evento("PagamentoRecusado", pedido_id=pedido_id, cliente=cliente, valor_total=valor,
                       motivo=___)]
```

> Dica: o status é `"RECUSADO"` e o motivo pode ser `"saldo insuficiente"`.

**Salve** (`Ctrl+S`).

## 🧪 Teste: o `bruno` tenta comprar um monitor

O `bruno` tem R$ 100 e o monitor custa R$ 900:

**`POST http://localhost:8031/pedidos`**

```json
{ "cliente": "bruno", "produto": "monitor", "quantidade": 1 }
```

```bash
curl -s -X POST localhost:8031/pedidos \
  -H 'Content-Type: application/json' \
  -d '{"cliente": "bruno", "produto": "monitor", "quantidade": 1}' \
  -w '← HTTP %{http_code}\n'
```

Veja a linha do tempo do pedido `bruno-1`:

```bash
curl -s localhost:8031/pedidos/bruno-1/historico
```

```text
+   0.0 s   pedidos    publicou  PedidoCriado
+   0.0 s   estoque    publicou  EstoqueReservado
+   0.0 s   pagamentos publicou  PagamentoRecusado
```

🤔 O pagamento foi recusado... mas o pedido continua `PENDENTE`:

```bash
curl -s localhost:8031/pedidos/bruno-1
```

O `pedidos` ainda não sabe reagir ao `PagamentoRecusado`. Guarde o `bruno-1`:
ele volta na Etapa 8.

## Clique em Verificar ✔
