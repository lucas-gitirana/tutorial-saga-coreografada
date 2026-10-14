#!/usr/bin/env bash
# Instala a extensão "Tutoriais Interativos de Microsserviços" a partir de um
# .vsix nesta pasta (nome no formato <nome>-<versão>.vsix).
# Executado no postAttachCommand: só nesse momento o VS Code já está conectado
# ao container e o comando 'code' está disponível.
PUBLISHER="lucas-gitirana"

if ! command -v code >/dev/null 2>&1; then
  echo "Comando 'code' indisponível; instale o .vsix manualmente (Extensions > ... > Install from VSIX)."
  exit 0
fi

instaladas=$(code --list-extensions --show-versions)

for vsix in .devcontainer/*.vsix; do
  [ -f "$vsix" ] || continue
  nome=$(basename "$vsix" .vsix)          # tutoriais-interativos-microsservicos-0.1.0
  versao=${nome##*-}                      # 0.1.0
  id="$PUBLISHER.${nome%-*}"              # lucas-gitirana.tutoriais-interativos-microsservicos
  if grep -qix "$id@$versao" <<<"$instaladas"; then
    echo "Extensão já instalada: $id@$versao"
    continue
  fi
  code --install-extension "$vsix" --force && echo "Extensão instalada: $vsix"
done
