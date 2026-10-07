#!/usr/bin/env bash
# Verificação automática da Etapa 09 (executada pela extensão ao clicar em Verificar).
# As checagens ficam em tutorial/verificacoes/etapa_09.py e usam só a biblioteca padrão do Python.
set -uo pipefail

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 não encontrado. As verificações precisam do Python 3 instalado na máquina (ou use o Codespaces)."
  exit 1
fi

python3 -B tutorial/verificacoes/etapa_09.py
