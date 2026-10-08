![Mapa: visão geral](tutorial/img/mapa-geral.svg)

📍 **Você está aqui:** conhecendo as peças do mapa.

## 1. Veja os containers

```bash
docker compose ps
```

Devem aparecer **4 containers** com estado `running (healthy)`:

| Container | No mapa |
| --- | --- |
| `pedidos` | começa a saga e guarda o desfecho (porta 8031) |
| `estoque` | reserva os produtos (porta 8032) |
| `pagamentos` | cobra o cliente (porta 8033) |
| `rabbitmq` | o "correio": por onde passam **todas as setas** (os eventos) |

O `docker-compose.yml`, aberto ao lado, descreve esses quatro containers.

## 2. Espie os bancos

Cada serviço tem o **seu** banco, e nenhum lê o banco do outro. Veja o do
estoque e o de pagamentos:

```bash
curl -s localhost:8032/estoque
curl -s localhost:8033/carteiras
```

Guarde dois números, eles vão importar: há só **2 monitores** no estoque, e o
**bruno** tem só **R$ 100** na carteira.

> 👀 Quer ver o correio por dentro? Abra o painel do RabbitMQ em
> <http://localhost:15672> (usuário e senha: `guest`) e clique em **Queues**.

> Algum container não está `healthy`? Rode `docker compose up -d --build --wait` de novo.

## 3. Clique em Verificar ✔

A verificação confere se os três serviços estão respondendo.
