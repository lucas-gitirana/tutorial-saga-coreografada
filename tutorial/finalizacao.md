# Parabéns, você implementou uma Saga Coreografada! 🎉

## O que você construiu

- Três serviços, **cada um com o seu banco**, que cooperam numa operação de
  negócio sem transação distribuída.
- **Transações locais** que publicam eventos e **reagem** aos eventos dos outros,
  sem nenhum coordenador central.
- Uma **transação de compensação** que mantém o sistema consistente quando o
  pagamento falha.
- Participantes **idempotentes**, que aguentam eventos entregues mais de uma vez.

## Benefícios e custos da coreografia

| Benefícios | Custos |
| --- | --- |
| Baixo acoplamento: cada serviço só conhece eventos | Difícil enxergar o fluxo inteiro (ele está espalhado pelos serviços) |
| Sem ponto central de falha | Risco de dependências cíclicas entre serviços |
| Desacoplamento temporal (serviço fora do ar ≠ falha) | Difícil saber "em que ponto" está uma saga |
| Fácil adicionar novos participantes | Compensações precisam ser pensadas e testadas para cada cenário |

Quando o fluxo cresce, muitas equipes trocam a coreografia por uma **saga
orquestrada**: um orquestrador central diz a cada serviço o que fazer.
Ferramentas como Temporal, Camunda e AWS Step Functions seguem essa linha.

## Para refletir

1. Neste tutorial, cada serviço grava no seu banco e **depois** publica o
   evento. O que acontece se ele cair entre as duas coisas? *(Pesquise o
   padrão Transactional Outbox, que atende ao primeiro princípio de Richardson.)*
2. Como o histórico (`/pedidos/<id>/historico`) ajuda a resolver o problema
   de "saber em que ponto está a saga"? Que ferramentas de observabilidade
   fariam isso em produção? *(Pesquise rastreamento distribuído.)*
3. Se surgir um serviço de **frete** que precisa calcular o envio antes do
   pagamento, quais serviços precisam mudar?

## Limpando o ambiente

```bash
docker compose down -v
```

O código completo de referência está na branch `solucao` deste repositório.
