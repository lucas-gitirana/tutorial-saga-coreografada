# Etapa 2 — O participante de pagamentos

**Objetivo:** implementar a transação local do serviço de pagamentos.

O arquivo `servicos/pagamentos/pagamentos.py` foi aberto ao lado. Para
entender o formato, olhe antes o exemplo pronto em
`servicos/estoque/estoque.py`, na função `ao_pedido_criado`.

## Como é um tratador de evento

```python
def ao_estoque_reservado(estado: dict, dados: dict) -> list:
    # estado -> o "banco de dados" do serviço (um dicionário)
    # dados  -> o conteúdo do evento recebido
    # retorno -> lista de eventos a publicar
```

O tratador **não sabe** quem vai reagir aos eventos que publica. Essa é a
essência da coreografia: cada serviço conhece só os eventos, não os outros serviços.

## O que implementar em `ao_estoque_reservado`

| Situação | O que fazer |
| --- | --- |
| `pedido_id` já está em `estado["pagamentos"]` | devolver `[]` (já processado) |
| saldo `<` valor | registrar o pagamento como `RECUSADO` e devolver `PagamentoRecusado` com um `motivo` |
| caso contrário | debitar o saldo, registrar como `APROVADO` e devolver `PagamentoAprovado` |

> **Por que verificar se já foi processado?** Sistemas de mensageria
> garantem entrega **pelo menos uma vez**: o mesmo evento pode chegar duas
> vezes (ex.: o serviço caiu antes de confirmar o recebimento). Um
> participante de saga precisa ser **idempotente**, ou cobraria o cliente em dobro.

## Teste no serviço

Reinicie o serviço. Ao subir, ele **reprocessa o evento pendente** da Etapa 1:

```bash
docker compose restart pagamentos && sleep 3
docker compose logs pagamentos --tail 5
```

A saga da `ana` continuou de onde parou:

```bash
PEDIDO_ANA=$(python3 -c 'import json; print(json.load(open("/tmp/pedido-ana.json"))["pedido_id"])')
curl -s localhost:8031/pedidos/$PEDIDO_ANA/historico
curl -s -w '\n' localhost:8031/pedidos/$PEDIDO_ANA
curl -s -w '\n' localhost:8033/carteiras
```

O pedido está `CONFIRMADO` e o saldo da `ana` caiu para R$ 700,00. O serviço
de pedidos já sabia tratar `PagamentoAprovado` (é o exemplo em `pedidos.py`).

Clique em **Verificar**. A verificação testa `pagamentos.py` diretamente.
