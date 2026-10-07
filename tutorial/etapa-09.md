![Mapa: compensação](tutorial/img/mapa-compensacao.svg)

📍 **Você está aqui:** dentro do `estoque`, na seta vermelha `PagamentoRecusado`.

## O que é COMPENSAR?

Numa saga **não existe *rollback***. A reserva do `bruno-1` já foi **gravada**
no banco do estoque, numa transação que terminou lá na Etapa 5. Não dá para
"voltar no tempo".

O que dá para fazer é uma **nova transação que anula o efeito da anterior**.
Pense no **estorno** de um cartão de crédito: a compra continua no extrato,
mas aparece uma linha nova, de crédito, que devolve o valor.

Veja o estoque de monitores ao longo da saga do `bruno-1`:

| Evento | Monitores disponíveis | Reserva `bruno-1` |
| --- | --- | --- |
| *(início)* | 2 | *(não existe)* |
| `PedidoCriado` → estoque **reserva** | 1 | `RESERVADA` |
| `PagamentoRecusado` → estoque **compensa** | 2 | `LIBERADA` |

A reserva não é apagada: ela muda para `LIBERADA`. Assim fica o registro do
que aconteceu, e uma segunda compensação do mesmo pedido pode ser ignorada.

## 🐍 Python rápido

| Código | Significa |
| --- | --- |
| `a is None or b != "X"` | verdadeiro se **qualquer um** dos dois for verdadeiro |
| `produto, quantidade = reserva["produto"], reserva["quantidade"]` | cria duas variáveis de uma vez |
| `estado["disponivel"].get(produto, 0)` | quantidade disponível, ou `0` se o produto não existe |

## ✏️ Faça

Abaixo do marcador **Etapa 9**, escreva o código e complete os `___`:

```python
    if reserva is None or reserva["status"] != "RESERVADA":
        return []    # nada a compensar (pedido sem reserva ou já compensado)

    produto, quantidade = reserva["produto"], reserva["quantidade"]
    estado["disponivel"][produto] = estado["disponivel"].get(produto, 0) + ___
    reserva["status"] = ___
    return [evento("EstoqueLiberado", pedido_id=dados["pedido_id"], produto=produto, quantidade=quantidade)]
```

**Salve** (`Ctrl+S`).

## 🧪 Teste

Ao salvar, o `estoque` reprocessa o `PagamentoRecusado` do `bruno-1`, pendente
desde a Etapa 5:

```bash
curl -s localhost:8032/estoque
```

Os monitores voltaram, e a reserva do `bruno-1` está `LIBERADA`. Veja quando a
compensação aconteceu:

```bash
curl -s localhost:8031/pedidos/bruno-1/historico
```

O `EstoqueLiberado` aparece **bem depois** dos outros eventos. O sistema passou
um tempo inconsistente e depois **convergiu**: isso é **consistência eventual**,
o preço de não ter uma transação única.

## Clique em Verificar ✔
