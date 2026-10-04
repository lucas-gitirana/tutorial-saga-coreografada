"""Mini-framework das verificações automáticas do tutorial.

Cada script verificar-etapa-NN.sh chama um arquivo etapa_NN.py, que registra
checagens com @verificacao("descrição") e termina chamando executar().
O código de saída é 0 quando todas passam e 1 caso contrário — é ele que a
extensão usa para marcar a etapa como correta ou incorreta.

Só usa a biblioteca padrão do Python (não precisa de pip install).
"""
from __future__ import annotations

import importlib
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parents[2]

_verificacoes: list[tuple[str, Callable[[], None]]] = []


def verificacao(descricao: str):
    def registrar(funcao: Callable[[], None]):
        _verificacoes.append((descricao, funcao))
        return funcao
    return registrar


def executar(parar_na_primeira_falha: bool = False) -> None:
    falhas = 0
    for descricao, funcao in _verificacoes:
        try:
            funcao()
        except AssertionError as erro:
            falhas += 1
            print(f"✘ {descricao}\n    → {erro}")
        except NotImplementedError as erro:
            falhas += 1
            print(f"✘ {descricao}\n    → ainda não implementado: {erro}")
        except Exception as erro:  # noqa: BLE001 - queremos mostrar qualquer erro ao aluno
            falhas += 1
            print(f"✘ {descricao}\n    → erro inesperado: {type(erro).__name__}: {erro}")
        else:
            print(f"✔ {descricao}")
            continue
        if parar_na_primeira_falha:
            break

    if falhas:
        print(f"\n{falhas} verificação(ões) falharam. Corrija e clique em Verificar de novo.")
        sys.exit(1)
    print("\nTudo certo! Etapa concluída.")
    sys.exit(0)


def importar(pasta_servico: str, modulo: str):
    """Importa um módulo Python de um serviço (ex.: 'servicos/pedidos-comando', 'comandos')."""
    caminho = str(RAIZ / pasta_servico)
    if caminho not in sys.path:
        sys.path.insert(0, caminho)
    return importlib.import_module(modulo)


# ---------------------------------------------------------------------------
# HTTP (para checar os serviços que estão rodando nos containers)
# ---------------------------------------------------------------------------
def http(metodo: str, url: str, corpo: dict | None = None, timeout: float = 10.0) -> tuple[int, object]:
    """Faz uma requisição e devolve (status, json). Não lança erro para 4xx/5xx."""
    dados = json.dumps(corpo).encode() if corpo is not None else None
    requisicao = urllib.request.Request(url, data=dados, method=metodo,
                                        headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(requisicao, timeout=timeout) as resposta:
            return resposta.status, _ler_json(resposta.read())
    except urllib.error.HTTPError as erro:
        return erro.code, _ler_json(erro.read())
    except (urllib.error.URLError, ConnectionError) as erro:
        raise AssertionError(
            f"não foi possível conectar em {url} ({getattr(erro, 'reason', erro)}). "
            "Os containers estão rodando? Confira com: docker compose ps"
        ) from None
    except TimeoutError:
        raise AssertionError(f"{url} não respondeu em {timeout:.0f}s.") from None


def _ler_json(conteudo: bytes) -> object:
    try:
        return json.loads(conteudo or b"null")
    except ValueError:
        return conteudo.decode(errors="replace")


def aguardar(condicao: Callable[[], object], segundos: float, intervalo: float = 0.5):
    """Repete ``condicao()`` até ela devolver algo verdadeiro ou o tempo acabar."""
    limite = time.monotonic() + segundos
    while True:
        resultado = condicao()
        if resultado or time.monotonic() >= limite:
            return resultado
        time.sleep(intervalo)
