![Mapa: desfechos de falha](tutorial/img/mapa-falhas.svg)

📍 **Você está aqui:** ainda no `pedidos`. Lembra do `bruno-1`, preso em
`PENDENTE` desde a Etapa 5?

## O evento que está esperando

Este é o `PagamentoRecusado` do `bruno-1`, pendente no `pedidos`:

```json
{
  "tipo": "PagamentoRecusado",
  "dados": { "pedido_id": "bruno-1", "cliente": "bruno", "valor_total": 900.0, "motivo": "saldo insuficiente" }
}
```

Diferente da Etapa 7, aqui o **motivo vem no evento**: quem sabe por que o
pagamento falhou é o `pagamentos`.

## ✏️ Faça

Abaixo do marcador **Etapa 8**, escreva o código (igual ao da Etapa 7) e
complete o `___`:

```python
    if pedido is None:
        return []
    pedido["status"] = "CANCELADO"
    pedido["motivo"] = ___         # o motivo que veio no evento
    return [evento("PedidoCancelado", pedido_id=pedido["pedido_id"], motivo=pedido["motivo"])]
```

> Dica: `dados["motivo"]` pega o valor da chave `"motivo"` dos dados do evento.

**Salve** (`Ctrl+S`).

## 🧪 Teste

```bash
curl -s localhost:8031/pedidos/bruno-1
```

O pedido do `bruno` está `CANCELADO` por `"saldo insuficiente"`. ✅
Agora olhe o estoque:

```bash
curl -s localhost:8032/estoque
```

```text
"disponivel": { "teclado": 8, "mouse": ..., "monitor": 1 },
"reservas": {
  "bruno-1": { "produto": "monitor", "quantidade": 1, "status": "RESERVADA" },
  ...
```

🤔 **1 monitor está preso** na reserva de um pedido **cancelado**. O sistema
ficou **inconsistente**: ninguém desfez o que o estoque fez. A próxima etapa
resolve isso.

> Reservas com nome `verif-...` foram criadas pelas verificações. Pode ignorá-las.

## Clique em Verificar ✔
