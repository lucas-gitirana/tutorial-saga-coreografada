#!/usr/bin/env bash
# Instala a extensão "Tutoriais Interativos de Microsserviços" a partir de um
# .vsix, se houver um nesta pasta (ex.: .devcontainer/tutoriais-interativos-microsservicos.vsix).
for vsix in .devcontainer/*.vsix; do
  [ -f "$vsix" ] || continue
  if command -v code >/dev/null 2>&1; then
    code --install-extension "$vsix" && echo "Extensão instalada: $vsix"
  else
    echo "Comando 'code' indisponível; instale $vsix manualmente (Extensions > ... > Install from VSIX)."
  fi
done
