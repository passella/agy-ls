#!/usr/bin/env bash
set -e

# Cores
GREEN='\033[1;32m'
BLUE='\033[1;34m'
RED='\033[1;31m'
RESET='\033[0m'

PREFIX="${PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"

echo -e "${BLUE}==> Instalando agy-ls...${RESET}"

# Garantir que o diretório bin existe
mkdir -p "$BIN_DIR"

# Copiar script agy-ls
SCRIPT_SRC="$(dirname "$0")/agy-ls"
if [ ! -f "$SCRIPT_SRC" ]; then
    echo -e "${RED}Erro: Arquivo 'agy-ls' não encontrado no diretório atual.${RESET}"
    exit 1
fi

cp "$SCRIPT_SRC" "$BIN_DIR/agy-ls"
chmod +x "$BIN_DIR/agy-ls"

echo -e "${GREEN}==> agy-ls instalado com sucesso em $BIN_DIR/agy-ls!${RESET}"

# Verificar se ~/.local/bin está no PATH
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "\n${RED}Aviso:${RESET} $BIN_DIR não está no seu \$PATH atual."
    echo "Adicione a seguinte linha ao seu ~/.bashrc ou ~/.zshrc:"
    echo -e "  ${BLUE}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
fi
