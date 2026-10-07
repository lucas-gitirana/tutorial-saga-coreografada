![Mapa: início da saga](tutorial/img/mapa-inicio.svg)

📍 **Você está aqui:** seguindo o pedido `ana-1` pelo mapa. Ele vai parar no
meio do caminho.

## 1. Veja a linha do tempo da saga

**`GET http://localhost:8031/pedidos/ana-1/historico`**

```bash
curl -s localhost:8031/pedidos/ana-1/historico
```

```text
+   0.0 s   pedidos    publicou  PedidoCriado
+   0.0 s   estoque    publicou  EstoqueReservado
```

Ninguém **mandou** o estoque reservar: ele **ouviu** o `PedidoCriado` e
reagiu. Isso é **coreografia**.

Depois disso... silêncio. O pedido continua `PENDENTE`.

## 2. Descubra onde travou

```bash
docker compose logs --no-log-prefix pagamentos --tail 3
```

```text
[pagamentos] ← recebeu EstoqueReservado (pedido ana-1)
[pagamentos] ⚠ EstoqueReservado NÃO tratado: ao_estoque_reservado ainda não devolve nada ...
```

O `pagamentos` recebeu o evento, mas o código de cobrança **ainda não existe**.
Quem vai escrever é você, na próxima etapa.

## 3. O evento não se perdeu

Um serviço só **confirma** ao Redis que tratou um evento depois de tratá-lo.
Sem confirmação, o evento fica guardado como **pendente**:

```bash
docker compose exec redis redis-cli XPENDING saga.eventos pagamentos
```

O primeiro número da saída é a quantidade de eventos pendentes do `pagamentos`: **1**.

Quando você escrever o código e **salvar**, o `pagamentos` reinicia, pega esse
evento de novo e a saga da `ana` **continua de onde parou**.

## 4. Clique em Verificar ✔
