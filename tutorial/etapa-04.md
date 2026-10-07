![Mapa: pagamentos](tutorial/img/mapa-pagamentos.svg)

📍 **Você está aqui:** dentro do `pagamentos`. Você vai escrever o tratador
`ao_estoque_reservado`, em três etapas curtas:

| Caso | Etapa |
| --- | --- |
| saldo suficiente: **cobrar e aprovar** | **esta** |
| saldo insuficiente: recusar | 5 |
| o mesmo evento chegou duas vezes: ignorar | 6 |

## O que entra e o que sai

Um **tratador** é uma função que recebe um evento, altera o banco do serviço e
devolve os eventos que quer publicar.

**Entra** (publicado pelo estoque):

```json
{
  "tipo": "EstoqueReservado",
  "dados": { "pedido_id": "ana-1", "cliente": "ana", "produto": "teclado", "quantidade": 2, "valor_total": 300.0 }
}
```

**Sai** (o `pedidos` vai ouvir):

```json
{
  "tipo": "PagamentoAprovado",
  "dados": { "pedido_id": "ana-1", "cliente": "ana", "valor_total": 300.0 }
}
```

O `pagamentos` não sabe **quem** vai ouvir o `PagamentoAprovado`. Ele só
publica. Cada serviço conhece **eventos**, não outros serviços.

## 🐍 Python rápido

| Código | Significa |
| --- | --- |
| `estado["saldos"][cliente] = 700.0` | troca o saldo do cliente no banco do serviço |
| `estado["pagamentos"][pedido_id] = {...}` | guarda um registro novo, na chave `pedido_id` |
| `return [evento("X", a=1)]` | termina a função devolvendo a lista de eventos a publicar. `evento("X", a=1)` vira `{"tipo": "X", "dados": {"a": 1}}` |

## ✏️ Faça

Abaixo do marcador **Etapa 4** (o último da função), escreva as 3 linhas e
complete os `___`:

```python
    estado["saldos"][cliente] = saldo - ___
    estado["pagamentos"][pedido_id] = {"cliente": cliente, "valor": valor, "status": "APROVADO"}
    return [evento("PagamentoAprovado", pedido_id=pedido_id, cliente=cliente, valor_total=___)]
```

> Atenção à **indentação**: 4 espaços, alinhado com `saldo = ...`.
> As variáveis `pedido_id`, `cliente`, `valor` e `saldo` já estão prontas no topo da função.

**Salve** o arquivo (`Ctrl+S`).

## 🧪 Teste: a saga da `ana` continua sozinha

Ao salvar, o `pagamentos` reinicia e pega o evento que estava **pendente**.
Espere 3 segundos e veja a linha do tempo:

```bash
curl -s localhost:8031/pedidos/ana-1/historico
```

```text
+   0.0 s   pedidos    publicou  PedidoCriado
+   0.0 s   estoque    publicou  EstoqueReservado
+  95.3 s   pagamentos publicou  PagamentoAprovado
+  95.3 s   pedidos    publicou  PedidoConfirmado
```

O `pedidos` já sabia reagir ao `PagamentoAprovado` (é o exemplo pronto em
`pedidos.py`) e **confirmou** o pedido. Confira o saldo da `ana`: deve ser **700**.

```bash
curl -s localhost:8033/carteiras
```

## Clique em Verificar ✔

> Deu erro de conexão? Pode ser um erro de digitação no Python. Veja com
> `docker compose logs pagamentos --tail 20`.
