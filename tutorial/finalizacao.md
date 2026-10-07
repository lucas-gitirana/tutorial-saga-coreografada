## Você montou a saga inteira 🎉

![Mapa da saga](tutorial/img/mapa-geral.svg)

| Peça do mapa | O que você fez |
| --- | --- |
| **Transação local** | `pagamentos` cobra ou recusa, grava no seu banco e publica um evento |
| **Idempotência** | o mesmo evento entregue duas vezes não cobra duas vezes |
| **Desfechos** | `pedidos` cancela quando falta estoque ou saldo |
| **Compensação** | `estoque` devolve a reserva de um pedido cujo pagamento falhou |
| **Desacoplamento temporal** | a saga esperou o `pagamentos` voltar e terminou sozinha |

## Vale a pena usar saga coreografada?

| ✅ Ganha | ⚠️ Paga |
| --- | --- |
| baixo acoplamento: cada serviço só conhece **eventos** | o fluxo fica **espalhado** pelos serviços: difícil enxergar o todo |
| sem ponto central de falha | difícil saber "em que ponto" está uma saga |
| um serviço fora do ar não derruba a compra | **consistência eventual**: o sistema passa por estados inconsistentes |
| fácil adicionar novos participantes | cada passo que pode falhar precisa de uma **compensação** pensada e testada |

Com poucos participantes, a coreografia é simples e elegante. Quando o fluxo
cresce, muitas equipes trocam para a **saga orquestrada**: um orquestrador
central diz a cada serviço o que fazer (ferramentas como Temporal, Camunda e
AWS Step Functions seguem essa linha).

## Para pensar

1. Cada serviço grava no seu banco e **depois** publica o evento. E se ele cair
   entre as duas coisas? *(Pesquise: padrão Transactional Outbox.)*
2. Se surgir um serviço de **frete**, que calcula o envio antes do pagamento,
   quais serviços precisam mudar?

## Limpando o ambiente

```bash
docker compose down -v
```

A solução completa está na branch `solucao` deste repositório.
