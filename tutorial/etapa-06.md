![Mapa: pagamentos](tutorial/img/mapa-pagamentos.svg)

📍 **Você está aqui:** ainda no `pagamentos`. E se o **mesmo evento** chegar
**duas vezes**?

## Por que isso acontece?

Sistemas de mensageria garantem entrega **pelo menos uma vez**, não
**exatamente uma vez**. Exemplo: o estoque publica o `EstoqueReservado`, a rede
falha antes da confirmação e ele publica **de novo**. Para o `pagamentos`, é o
mesmo evento chegando duas vezes.

## 🧪 Primeiro, veja o problema

O saldo da `ana` agora é **700**. Simule a reentrega do `EstoqueReservado` do
pedido `ana-1`:

```bash
curl -s -X POST localhost:8033/simular/reentrega/ana-1
sleep 1
curl -s localhost:8033/carteiras
```

😱 O saldo da `ana` caiu para **400**: ela foi cobrada **duas vezes** pelo
mesmo pedido.

## Idempotência

Uma operação é **idempotente** quando fazê-la 2, 3 ou 10 vezes dá o **mesmo
resultado** que fazê-la uma vez. É como o botão do elevador: apertar de novo
não chama outro elevador.

No `pagamentos`, a regra é simples: **se já existe registro deste `pedido_id`,
o pedido já foi cobrado. Ignore o evento.**

## ✏️ Faça

Abaixo do marcador **Etapa 6** (o primeiro da função), complete o `___`:

```python
    if pedido_id in estado[___]:
        return []    # já processado: não cobra de novo e não publica nada
```

> Dica: os registros de pagamento ficam em `estado["pagamentos"]`.

**Salve** (`Ctrl+S`).

## 🧪 Teste de novo

```bash
curl -s -X POST localhost:8033/simular/reentrega/ana-1
sleep 1
curl -s localhost:8033/carteiras
```

O saldo da `ana` continua **400**. A cobrança extra do teste anterior fica de
lembrança. 😉

> O `estoque` (`if pedido_id in estado["reservas"]`) e o `pedidos`
> (`_pedido_pendente`) já se protegiam assim. **Todo participante de uma saga
> precisa ser idempotente.**

## Clique em Verificar ✔
