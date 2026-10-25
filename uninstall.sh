#!/usr/bin/env bash
set -e

# Cores
GREEN='\033[1;32m'
BLUE='\033[1;34m'
RED='\033[1;31m'
RESET='\033[0m'

PREFIX="${PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
TARGET="$BIN_DIR/agy-ls"

echo -e "${BLUE}==> Removendo agy-ls...${RESET}"

if [ -f "$TARGET" ]; then
    rm -f "$TARGET"
    echo -e "${GREEN}==> $TARGET removido com sucesso!${RESET}"
else
    echo -e "${RED}agy-ls não foi encontrado em $TARGET.${RESET}"
fi
