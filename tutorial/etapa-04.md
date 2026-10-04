# Etapa 4 — Transação de compensação

**Objetivo:** desfazer a reserva de estoque quando o pagamento é recusado.

Numa saga não existe *rollback*: a reserva **já foi gravada** no banco do
estoque. O que dá para fazer é executar uma nova transação que **compensa** a
anterior. Cada ação da saga que pode precisar ser desfeita tem a sua
compensação:

| Ação | Compensação |
| --- | --- |
| reservar estoque (`ao_pedido_criado`) | liberar a reserva (`ao_pagamento_recusado`) |

## O que implementar em `ao_pagamento_recusado`

No arquivo `servicos/estoque/estoque.py`:

1. Encontre a reserva pelo **id de correlação**:
   `estado["reservas"].get(dados["pedido_id"])`. O evento `PagamentoRecusado`
   nem traz o produto. É o estoque que sabe, pelos **seus próprios dados**, o
   que reservou para aquele pedido.
2. Se a reserva não existe ou não está `"RESERVADA"`, devolva `[]`
   (idempotência: nada a compensar).
3. Devolva a quantidade para `estado["disponivel"][produto]` e mude o status
   da reserva para `"LIBERADA"`.
4. Publique `EstoqueLiberado` com `pedido_id`, `produto` e `quantidade`.

## Teste no serviço

Ao reiniciar, o estoque reprocessa o `PagamentoRecusado` do bruno, que ficou
pendente na Etapa 3:

```bash
docker compose restart estoque && sleep 3
curl -s -w '\n' localhost:8032/estoque
```

Os 2 monitores estão disponíveis de novo, e a reserva do bruno aparece como `LIBERADA`.

```bash
PEDIDO_BRUNO=$(python3 -c 'import json; print(json.load(open("/tmp/pedido-bruno.json"))["pedido_id"])')
curl -s localhost:8031/pedidos/$PEDIDO_BRUNO/historico
```

O `EstoqueLiberado` aparece bem depois dos outros eventos: a compensação
aconteceu **eventualmente**. Em uma saga, o sistema passa por estados
intermediários inconsistentes e converge para a consistência.

Clique em **Verificar**. A verificação testa `estoque.py` diretamente.
