# agy-ls 🚀

Navegador e seletor interativo de conversas e sessões do **Antigravity CLI (`agy`)**.

O `agy-ls` permite inspecionar, buscar, listar e navegar pelas conversas e prompts do Antigravity salvos no banco SQLite local (`conversation_summaries.db`) e nos diretórios de brain (`brain/`).

---

## 🛠️ Instalação Rápida

### Opção 1: Via script de instalação (`install.sh`)
```bash
git clone https://github.com/passella/agy-ls.git
cd agy-ls
./install.sh
```

### Opção 2: Via pipx / pip (desenvolvimento)
```bash
pip install .
```

---

## 💡 Uso e Exemplos

Execute diretamente no terminal:
```bash
agy-ls
```

### Opções e Flags disponíveis:
- `-h, --help`: Exibe a ajuda.
- `-l, --list, --no-interactive`: Modo estático (exibe listagem tabular sem seletor interativo).
- `-n, --limit LIMIT`: Limita a quantidade de conversas consultadas.
- `--preview CID`: Exibe prévia detalhada da conversa informada (`CID`).
- `--curses`: Força o uso do menu curses em vez do `fzf`.
- `--fzf`: Força o uso do `fzf`.

---

## 🗑️ Desinstalação

```bash
./uninstall.sh
```

---

## 📄 Licença
Distribuído sob a licença MIT.
