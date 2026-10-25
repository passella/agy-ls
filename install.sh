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
PRIMARY_URL="https://passella.github.io/agy-ls/agy-ls"
FALLBACK_URL="https://raw.githubusercontent.com/passella/agy-ls/master/agy-ls"

echo -e "${BLUE}==> Instalando agy-ls...${RESET}"

# 1. Verificar pré-requisitos (python3)
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Erro: python3 não está instalado no sistema. O agy-ls requer Python 3.${RESET}"
    exit 1
fi

# 2. Garantir que o diretório bin existe
mkdir -p "$BIN_DIR"

# 3. Suporte Híbrido: Local vs Remoto (curl | bash)
SCRIPT_SRC="$(dirname "$0")/agy-ls"
TARGET_FILE="$BIN_DIR/agy-ls"

if [ -f "$SCRIPT_SRC" ]; then
    echo -e "${BLUE}--> Encontrado script localmente. Copiando de $SCRIPT_SRC...${RESET}"
    cp "$SCRIPT_SRC" "$TARGET_FILE"
else
    echo -e "${BLUE}--> Baixando agy-ls de $PRIMARY_URL...${RESET}"
    DOWNLOAD_SUCCESS=false
    if command -v curl &> /dev/null; then
        if curl -fsSL "$PRIMARY_URL" -o "$TARGET_FILE"; then
            DOWNLOAD_SUCCESS=true
        else
            echo -e "${YELLOW}--> Falha ao baixar de $PRIMARY_URL. Tentando fallback para $FALLBACK_URL...${RESET}"
            if curl -fsSL "$FALLBACK_URL" -o "$TARGET_FILE"; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    elif command -v wget &> /dev/null; then
        if wget -qO "$TARGET_FILE" "$PRIMARY_URL"; then
            DOWNLOAD_SUCCESS=true
        else
            echo -e "${YELLOW}--> Falha ao baixar de $PRIMARY_URL. Tentando fallback para $FALLBACK_URL...${RESET}"
            if wget -qO "$TARGET_FILE" "$FALLBACK_URL"; then
                DOWNLOAD_SUCCESS=true
            fi
        fi
    else
        echo -e "${RED}Erro: Nem curl nem wget foram encontrados para baixar o agy-ls remotamente.${RESET}"
        exit 1
    fi

    if [ "$DOWNLOAD_SUCCESS" != "true" ]; then
        echo -e "${RED}Erro: Falha ao baixar agy-ls tanto da URL principal quanto do fallback.${RESET}"
        exit 1
    fi
fi

chmod +x "$TARGET_FILE"

# 4. Garantia de PATH Permanente em Novos Terminais
PATH_EXPORT='export PATH="$HOME/.local/bin:$PATH"'
SHELL_CONFIGS=("$HOME/.bashrc" "$HOME/.zshrc" "$HOME/.profile")
UPDATED_CONFIGS=()

for rc in "${SHELL_CONFIGS[@]}"; do
    # Se o arquivo existe OU se for .bashrc/.zshrc padrão do usuário
    if [ -f "$rc" ] || [ "$rc" = "$HOME/.bashrc" ] || [ "$rc" = "$HOME/.zshrc" ]; then
        touch "$rc" 2>/dev/null || true
        if [ -f "$rc" ]; then
            if ! grep -q "\.local/bin" "$rc"; then
                echo -e "\n# Adicionado pelo instalador do agy-ls" >> "$rc"
                echo "$PATH_EXPORT" >> "$rc"
                UPDATED_CONFIGS+=("$rc")
            fi
        fi
    fi
done

# 5. Mensagem de Conclusão e Instruções
echo -e "${GREEN}==> agy-ls instalado com sucesso em $TARGET_FILE!${RESET}"

if [ ${#UPDATED_CONFIGS[@]} -gt 0 ]; then
    echo -e "${YELLOW}Configuração de PATH:${RESET} Adicionado automaticamente em: ${UPDATED_CONFIGS[*]}"
fi

# Verificar se ~/.local/bin está no PATH da sessão atual
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "\n${YELLOW}Aviso:${RESET} $BIN_DIR não está no seu \$PATH atual desta sessão."
    echo -e "Para usar imediatamente nesta sessão, execute:"
    echo -e "  ${BLUE}export PATH=\"\$HOME/.local/bin:\$PATH\"${RESET}"
    echo -e "Nos próximos terminais, isso funcionará automaticamente."
else
    echo -e "${GREEN}Tudo pronto! Você já pode executar:${RESET} ${BLUE}agy-ls${RESET}"
fi
