# Tutorial interativo: padrão Saga Coreografada

Tutorial prático da disciplina de DevOps (UDESC) sobre o padrão **Saga
Coreografada**. Três microsserviços (pedidos, estoque e pagamentos), cada um
com o seu banco, cooperam numa compra por meio de eventos, sem orquestrador
central. Quando o pagamento falha, uma transação de compensação desfaz a
reserva de estoque.

**Duração estimada:** 40 minutos · 5 etapas com avaliação automática.

## Como começar

### Opção 1: GitHub Codespaces (recomendado)

1. Clique em **Code → Codespaces → Create codespace on main**.
2. Aguarde o ambiente abrir. Docker e Python já vêm instalados.
3. Instale a extensão **Tutoriais Interativos de Microsserviços** (veja abaixo).

### Opção 2: na sua máquina

Pré-requisitos: [VS Code](https://code.visualstudio.com/), Docker com Docker
Compose v2, Python 3.9+ e `bash` (Linux, macOS ou WSL no Windows).

```bash
git clone <url-deste-repositorio>
code tutorial-saga-coreografada
```

### Instalando a extensão

Baixe o arquivo `.vsix` da extensão
[Tutoriais Interativos de Microsserviços](https://github.com/lucas-gitirana/tutoriais-interativos-microsservicos)
e instale em **Extensions → ⋯ → Install from VSIX...**. Ao abrir esta pasta, o
tutorial aparece na aba **Tutoriais Interativos** da barra lateral. Clique em
**Executar tutorial**.

## Estrutura

```text
index.json                 definição do tutorial (lida pela extensão)
docker-compose.yml         redis + pedidos (8031) + estoque (8032) + pagamentos (8033)
servicos/
  pedidos/pedidos.py       inicia a saga e registra o desfecho
  estoque/estoque.py       reserva e compensa (libera) o estoque
  pagamentos/pagamentos.py cobra o cliente
  comum/                   infraestrutura compartilhada (barramento Redis Streams)
tutorial/
  *.md                     texto de cada etapa
  verificar-etapa-NN.sh    avaliação automática de cada etapa
  verificacoes/            checagens em Python (só biblioteca padrão)
```

## Problemas comuns

| Sintoma | O que fazer |
| --- | --- |
| `Connection refused` nas verificações | `docker compose up -d --build --wait` e confira `docker compose ps` |
| Alterei o código e nada mudou | reinicie o serviço: `docker compose restart <servico>` |
| Pedido parado em `PENDENTE` | veja a linha do tempo: `curl localhost:8031/pedidos/<id>/historico` e os logs: `docker compose logs <servico>` |
| Quero recomeçar do zero | `docker compose down -v && docker compose up -d --build --wait` |

O código completo de referência fica na branch **`solucao`**.
