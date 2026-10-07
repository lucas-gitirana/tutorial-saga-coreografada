## O problema

Numa loja online, **uma compra** mexe em **três serviços**, e cada um tem o
**seu próprio banco de dados**:

| Serviço | O que faz na compra |
| --- | --- |
| **pedidos** | registra o pedido |
| **estoque** | reserva o produto |
| **pagamentos** | cobra o cliente |

Num sistema com um banco só, uma **transação** resolveria: ou tudo acontece, ou
nada acontece. Mas não existe transação que abrace **três bancos diferentes**.

E se o pagamento falhar **depois** que o estoque já reservou o produto?
**Quem desfaz a reserva?**

## A ideia da Saga

Uma **saga** quebra a compra em **transações locais**, uma em cada serviço.
Cada serviço faz a sua parte, grava no seu banco e **avisa** o próximo com um
**evento**. Se um passo falha, os anteriores são desfeitos por **transações de
compensação**:

```text
deu certo:    pedidos cria ─▶ estoque reserva ─▶ pagamentos cobra  ─▶ pedidos CONFIRMA ✔
deu errado:   pedidos cria ─▶ estoque reserva ─▶ pagamentos RECUSA ─▶ pedidos CANCELA  ✘
                                    ▲                    │
                                    └────────────────────┘  estoque DEVOLVE a reserva (compensação)
```

## Coreografada: sem maestro

Existem dois jeitos de coordenar uma saga:

| | Orquestrada | **Coreografada** (este tutorial) |
| --- | --- | --- |
| Parece com | uma orquestra: o **maestro** diz quem toca e quando | uma dança: cada dançarino **ouve a música** e reage aos outros |
| Na prática | um serviço central manda cada um fazer a sua parte | ninguém manda: cada serviço **escuta eventos** e reage |

Este é o mapa da saga que você vai construir. Ele aparece em toda etapa,
destacando a parte em que você está:

![Mapa da saga](tutorial/img/mapa-geral.svg)

| Evento | Quem publica | Quem reage |
| --- | --- | --- |
| `PedidoCriado` | pedidos | estoque tenta reservar |
| `EstoqueReservado` | estoque | pagamentos tenta cobrar |
| `EstoqueIndisponivel` | estoque | pedidos cancela |
| `PagamentoAprovado` | pagamentos | pedidos confirma |
| `PagamentoRecusado` | pagamentos | pedidos cancela **e** estoque **compensa** |

## As ferramentas

| Peça | O que é | Papel aqui |
| --- | --- | --- |
| **Docker Compose** | sobe vários containers com um único comando, a partir do `docker-compose.yml` | liga os 4 containers |
| **Flask** | microframework web em Python | faz a API HTTP de cada serviço |
| **Arquivo JSON** | um arquivo em um volume Docker separado para cada serviço | o **banco próprio** de cada serviço |
| **Redis** | banco em memória, muito rápido. Tem os *Streams*: listas de mensagens que só crescem, sempre em ordem | **barramento de eventos**: todas as setas do mapa passam por ele |
| **curl** | faz requisições HTTP pelo terminal | é o "cliente" que você vai usar |

## Como funciona este tutorial

- **▶ Executar**, embaixo de um bloco de comando, roda o comando no terminal.
- **Verificar** confere o seu código e diz o que falta quando algo dá errado.
- O arquivo a editar abre sozinho, ao lado. Procure o marcador **✏️**.
- Os serviços recarregam sozinhos quando você **salva** um arquivo (`Ctrl+S`).

## Preparando o ambiente

Ao abrir esta tela, o terminal já começou a rodar:

```bash
docker compose up -d --build --wait
```

- `up`: cria e liga os containers descritos no `docker-compose.yml`;
- `-d`: roda em segundo plano e devolve o terminal para você;
- `--build`: constrói a imagem dos serviços Python antes de subir;
- `--wait`: só termina quando todos os serviços estiverem **saudáveis**
  (respondendo). Assim você não começa com o ambiente pela metade.

Na primeira vez demora 1 ou 2 minutos, porque as imagens são baixadas. Quando o
terminal voltar ao prompt, clique em **Começar**.

> Pré-requisitos: Docker com Docker Compose e Python 3 (usado pelas
> verificações). No GitHub Codespaces já vem tudo instalado.
