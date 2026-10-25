#!/usr/bin/env bash
set -e

# Cores ANSI
GREEN='\033[1;32m'
BLUE='\033[1;34m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
RESET='\033[0m'

PREFIX="${PREFIX:-$HOME/.local}"
BIN_DIR="$PREFIX/bin"
TARGET="$BIN_DIR/agy-ls"

echo -e "${BLUE}==> Removendo agy-ls...${RESET}"

# 1. Remover binário agy-ls
if [ -f "$TARGET" ] || [ -L "$TARGET" ]; then
    rm -f "$TARGET"
    echo -e "${GREEN}==> Binário $TARGET removido com sucesso!${RESET}"
else
    echo -e "${YELLOW}==> Aviso: Binário $TARGET não encontrado (já desinstalado ou em outro caminho).${RESET}"
fi

# 2. Limpar configurações de PATH adicionadas ao shell
echo -e "${BLUE}==> Verificando arquivos de configuração de shell...${RESET}"

SHELL_CONFIGS=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile")
CLEANED_CONFIGS=()

for rc in "${SHELL_CONFIGS[@]}"; do
    if [ -f "$rc" ]; then
        if grep -q "Adicionado pelo instalador do agy-ls" "$rc"; then
            tmp_file="$(mktemp "${rc}.XXXXXX")"
            awk '
            /#[[:space:]]*Adicionado pelo instalador do agy-ls/ {
                skip=3
                next
            }
            skip > 0 && /^[[:space:]]*$/ {
                skip--
                next
            }
            skip > 0 && /export PATH=.*\.local\/bin/ {
                skip=0
                next
            }
            skip > 0 {
                skip=0
            }
            {
                print
            }
            ' "$rc" > "$tmp_file"

            if ! cmp -s "$tmp_file" "$rc"; then
                chmod --reference="$rc" "$tmp_file" 2>/dev/null || true
                mv "$tmp_file" "$rc"
                CLEANED_CONFIGS+=("$rc")
            else
                rm -f "$tmp_file"
            fi
        fi
    fi
done

if [ ${#CLEANED_CONFIGS[@]} -gt 0 ]; then
    echo -e "${GREEN}==> Entradas de configuração removidas de: ${CLEANED_CONFIGS[*]}${RESET}"
else
    echo -e "${BLUE}--> Nenhuma entrada residual do agy-ls encontrada em arquivos de shell.${RESET}"
fi

echo -e "\n${GREEN}==> agy-ls desinstalado com sucesso!${RESET}"
