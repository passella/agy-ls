#!/usr/bin/env python3
import os
import sys
import json
import sqlite3
import shutil
import subprocess
import argparse
import re
import signal
from datetime import datetime

# Prevent broken pipe errors on head / grep
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except Exception:
    pass

DB_PATH = os.path.expanduser('~/.gemini/antigravity-cli/conversation_summaries.db')
BRAIN_DIR = os.path.expanduser('~/.gemini/antigravity-cli/brain')

# ANSI colors for preview and terminal
CYAN = '\033[1;36m'
GREEN = '\033[1;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[1;34m'
MAGENTA = '\033[1;35m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'

def get_transcript_summary(cid, is_subagent=False):
    trans_path = os.path.join(BRAIN_DIR, cid, '.system_generated', 'logs', 'transcript.jsonl')
    if not os.path.exists(trans_path):
        return None, None
    
    first_user_content = None
    system_task = None
    
    try:
        with open(trans_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    obj = json.loads(line)
                    t = obj.get('type')
                    content = obj.get('content', '')
                    
                    if t == 'SYSTEM_MESSAGE':
                        # Check if it contains a subagent task prompt
                        if '<SYSTEM_MESSAGE>' in content or '[SUBAGENT_TASK]' in content:
                            parts = content.split('content=')
                            if len(parts) > 1:
                                system_task = parts[1].strip()
                            else:
                                system_task = content.strip()
                            if is_subagent and system_task:
                                break
                    elif t == 'USER_INPUT' and not first_user_content:
                        first_user_content = content.strip()
                        if not is_subagent:
                            break
                except:
                    pass
    except:
        pass
    
    # Clean up system_task if it contains header info
    if system_task:
        lines = system_task.splitlines()
        clean_lines = []
        for l in lines:
            if not l.startswith('[Message]') and not l.startswith('The following is') and not l.startswith('<SYSTEM_MESSAGE>'):
                clean_lines.append(l)
        
        summary = ' '.join(clean_lines).strip()
        if summary.startswith('content='):
            summary = summary[8:].strip()
            
        summary = re.sub(r'^\s*\[SUBAGENT_TASK\]\s*', '', summary)
        summary = re.sub(r'^AGENT_ID:\s*\S+\s*', '', summary)
        summary = re.sub(r'^AGENT_DEF:\s*\S+\s*', '', summary)
        summary = re.sub(r'^TASK:\s*', '', summary, flags=re.IGNORECASE)
        summary = re.sub(r'\[SUBAGENT_TASK\]', '', summary)
        summary = re.sub(r'AGENT_ID:\s*\S+', '', summary)
        summary = re.sub(r'AGENT_DEF:\s*\S+', '', summary)
        summary = re.sub(r'\bTASK:\s*', '', summary, flags=re.IGNORECASE)
        summary = re.sub(r'</SYSTEM_MESSAGE>.*$', '', summary, flags=re.DOTALL)
        summary = ' '.join(summary.split())
        
        if summary:
            return summary, 'SUBAGENT'
            
    if first_user_content:
        clean = first_user_content.replace('<USER_REQUEST>', '').replace('</USER_REQUEST>', '').strip()
        clean = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>', '', clean)
        clean = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*?</USER_SETTINGS_CHANGE>', '', clean)
        lines = [l.strip() for l in clean.splitlines() if l.strip()]
        if lines:
            return lines[0], 'USER'
            
    return None, None

def load_conversations(limit=None):
    if not os.path.exists(DB_PATH):
        print(f"Banco de dados não encontrado em {DB_PATH}", file=sys.stderr)
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    query = """
        SELECT conversation_id, title, preview, last_modified_time, parent_conversation_id, agent_name
        FROM conversation_summaries
        ORDER BY last_modified_time DESC
    """
    if limit and limit > 0:
        query += f" LIMIT {int(limit)}"
        
    rows = cursor.execute(query).fetchall()
    conn.close()

    items = []
    for row in rows:
        cid, title, preview, mod_time, parent_id, agent_name = row
        display_text = title or preview
        conv_type = "USER" if not parent_id else f"SUB ({agent_name or 'sub'})"
        
        if not display_text:
            trans_summary, inferred_type = get_transcript_summary(cid, is_subagent=bool(parent_id))
            if trans_summary:
                display_text = trans_summary
                if inferred_type and not parent_id:
                    conv_type = inferred_type
            else:
                display_text = "(Sem resumo disponível)"
                
        try:
            dt = datetime.fromisoformat(mod_time.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            time_str = mod_time[:19] if mod_time else "N/A"
            
        short_summary = display_text.replace('\n', ' ')
        if len(short_summary) > 65:
            short_summary_static = short_summary[:62] + "..."
        else:
            short_summary_static = short_summary
            
        items.append({
            'cid': cid,
            'title': title,
            'preview': preview,
            'mod_time': mod_time,
            'parent_id': parent_id,
            'agent_name': agent_name,
            'time_str': time_str,
            'conv_type': conv_type,
            'full_summary': display_text,
            'short_summary': short_summary,
            'short_summary_static': short_summary_static,
        })
    return items

def build_table_lines(items):
    header_lines = [
        f"{'DATA / HORA':<22} | {'TIPO':<10} | {'ID':<36} | {'RESUMO / TÍTULO REAL':<65}",
        "-" * 141
    ]
    data_lines = []
    for it in items:
        line = f"{it['time_str']:<22} | {it['conv_type']:<10} | {it['cid']:<36} | {it['short_summary_static']:<65}"
        data_lines.append(line)
    return header_lines, data_lines

def print_static_table(items):
    header_lines, data_lines = build_table_lines(items)
    try:
        for hl in header_lines:
            print(hl)
        for dl in data_lines:
            print(dl)
    except BrokenPipeError:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        sys.exit(0)

def render_preview(cid):
    cid = cid.strip()
    if not cid:
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    row = c.execute('''
        SELECT conversation_id, title, preview, last_modified_time, parent_conversation_id, agent_name, workspace_uris, step_count
        FROM conversation_summaries WHERE conversation_id = ?
    ''', (cid,)).fetchone()
    conn.close()
    
    if not row:
        print(f"{YELLOW}Conversa {cid} não encontrada no banco.{RESET}")
        return
        
    cid, title, prev, mod_time, parent_id, agent_name, ws_uris, steps = row
    
    try:
        dt = datetime.fromisoformat(mod_time.replace('Z', '+00:00'))
        time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
    except:
        time_str = mod_time[:19] if mod_time else 'N/A'
        
    try:
        ws = json.loads(ws_uris)
        ws_clean = ', '.join([w.replace('file://', '') for w in ws])
    except:
        ws_clean = ws_uris or 'N/A'
        
    conv_type = 'USER' if not parent_id else f'SUBAGENT ({agent_name or "sub"})'

    print(f"{CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{RESET}")
    print(f"{CYAN}┃{RESET} {BOLD}ID:{RESET}   {GREEN}{cid}{RESET}")
    print(f"{CYAN}┃{RESET} {BOLD}DATA:{RESET} {time_str}  |  {BOLD}TIPO:{RESET} {conv_type}  |  {BOLD}PASSOS:{RESET} {steps}")
    if parent_id:
        print(f"{CYAN}┃{RESET} {BOLD}PARENT CONV:{RESET} {parent_id}")
    print(f"{CYAN}┃{RESET} {BOLD}WORKSPACE:{RESET}   {ws_clean}")
    print(f"{CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{RESET}")
    
    trans_path = os.path.join(BRAIN_DIR, cid, '.system_generated', 'logs', 'transcript.jsonl')
    if not os.path.exists(trans_path):
        print(f"\n{DIM}(Sem arquivo de transcrição disponível){RESET}")
        return
        
    entries = []
    with open(trans_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except:
                pass
                
    if parent_id:
        # Subagent
        task_text = ''
        for e in entries:
            if e.get('type') == 'SYSTEM_MESSAGE':
                cnt = e.get('content', '')
                if 'content=' in cnt:
                    task_text = cnt.split('content=')[1].strip()
                elif '[SUBAGENT_TASK]' in cnt:
                    task_text = cnt.strip()
                if task_text:
                    break
        if task_text:
            task_text = re.sub(r'</SYSTEM_MESSAGE>.*$', '', task_text, flags=re.DOTALL).strip()
            print(f"\n{YELLOW}🎯 TAREFA DO SUBAGENTE:{RESET}")
            print(f"{DIM}{task_text}{RESET}")
    else:
        # User
        user_inputs = []
        for e in entries:
            if e.get('type') == 'USER_INPUT':
                c = e.get('content', '')
                c = re.sub(r'<USER_REQUEST>([\s\S]*?)</USER_REQUEST>', r'\1', c)
                c = re.sub(r'<ADDITIONAL_METADATA>[\s\S]*?</ADDITIONAL_METADATA>', '', c)
                c = re.sub(r'<USER_SETTINGS_CHANGE>[\s\S]*?</USER_SETTINGS_CHANGE>', '', c)
                c = c.strip()
                if c:
                    user_inputs.append(c)
        if user_inputs:
            print(f"\n{YELLOW}💬 PRIMEIRO PEDIDO DO USUÁRIO:{RESET}")
            print(user_inputs[0][:400])
            if len(user_inputs) > 1:
                print(f"\n{YELLOW}💬 ÚLTIMO PEDIDO ({len(user_inputs)} mensagens do usuário):{RESET}")
                print(user_inputs[-1][:400])
                
        # Subagents spawned
        subagents_dir = os.path.join(BRAIN_DIR, cid, '.system_generated', 'subagents')
        if os.path.exists(subagents_dir):
            subs = []
            for f in sorted(os.listdir(subagents_dir)):
                if f.endswith('.json'):
                    try:
                        with open(os.path.join(subagents_dir, f)) as sf:
                            sdata = json.load(sf)
                            role = sdata.get('subagentDescriptor', {}).get('role', 'subagent')
                            subs.append(f"{role} ({f[:-5]})")
                    except:
                        pass
            if subs:
                print(f"\n{MAGENTA}🤖 SUBAGENTES DISPARADOS ({len(subs)}):{RESET}")
                for s in subs[:6]:
                    print(f"  • {s}")
                if len(subs) > 6:
                    print(f"  • ... e mais {len(subs)-6} subagente(s)")

def select_with_fzf(items, script_path):
    fzf_bin = shutil.which('fzf')
    if not fzf_bin:
        return None

    header_lines, data_lines = build_table_lines(items)
    
    cmd = [
        fzf_bin,
        '--ansi',
        '--reverse',
        '--height=90%',
        f'--header-lines={len(header_lines)}',
        '--delimiter=|',
        '--prompt=🔍 Selecione a conversa > ',
        '--header=↑/↓: Navegar | ENTER: Abrir no agy | ESC/Ctrl+C: Sair | Digite para filtrar',
        f'--preview={sys.executable} \'{script_path}\' --preview {{3}}',
        '--preview-window=right:55%:wrap',
        '--border',
        '--info=inline',
    ]

    input_text = '\n'.join(header_lines + data_lines)

    try:
        proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        stdout, _ = proc.communicate(input=input_text)
        if proc.returncode != 0 or not stdout.strip():
            return None
            
        parts = stdout.strip().split('|')
        if len(parts) >= 3:
            return parts[2].strip()
        return None
    except (KeyboardInterrupt, subprocess.SubprocessError):
        return None

def select_with_curses(items):
    import curses

    if not items:
        print("Nenhuma conversa encontrada.")
        return None

    def curses_main(stdscr):
        try:
            curses.curs_set(0)
        except Exception:
            pass
        try:
            curses.use_default_colors()
        except Exception:
            pass
        try:
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_CYAN, -1)
            curses.init_pair(3, curses.COLOR_YELLOW, -1)
        except Exception:
            pass

        selected_idx = 0
        scroll_offset = 0

        while True:
            stdscr.clear()
            max_y, max_x = stdscr.getmaxyx()

            if max_y < 5 or max_x < 40:
                stdscr.addstr(0, 0, "Terminal muito pequeno!")
                stdscr.refresh()
                key = stdscr.getch()
                if key in (27, ord('q'), ord('Q')):
                    return None
                continue

            # Header title
            title = " 🔍 SELEÇÃO DE CONVERSAS AGY "
            try:
                stdscr.addstr(0, 0, title[:max_x], curses.A_BOLD | curses.color_pair(2))
            except:
                stdscr.addstr(0, 0, title[:max_x])

            # Header column
            col_hdr = f"{'DATA / HORA':<20} | {'TIPO':<10} | {'ID':<36} | {'RESUMO':<40}"
            try:
                stdscr.addstr(1, 0, col_hdr[:max_x], curses.A_UNDERLINE)
            except:
                stdscr.addstr(1, 0, col_hdr[:max_x])

            # Bottom hint
            hint = " [↑/↓] Navegar | [PgUp/PgDn] Rolar | [ENTER] Abrir | [q/ESC] Sair "
            if max_y > 1:
                try:
                    stdscr.addstr(max_y - 1, 0, hint[:max_x - 1], curses.color_pair(3))
                except:
                    pass

            visible_lines = max_y - 3
            if visible_lines <= 0:
                visible_lines = 1

            if selected_idx < scroll_offset:
                scroll_offset = selected_idx
            elif selected_idx >= scroll_offset + visible_lines:
                scroll_offset = selected_idx - visible_lines + 1

            for i in range(visible_lines):
                item_idx = scroll_offset + i
                if item_idx >= len(items):
                    break

                row = items[item_idx]
                line_str = f"{row['time_str']:<20} | {row['conv_type']:<10} | {row['cid']:<36} | {row['short_summary']}"
                line_str = line_str[:max_x - 1]

                y = 2 + i
                try:
                    if item_idx == selected_idx:
                        stdscr.addstr(y, 0, line_str, curses.A_BOLD | curses.color_pair(1))
                    else:
                        stdscr.addstr(y, 0, line_str)
                except:
                    pass

            stdscr.refresh()

            key = stdscr.getch()
            if key == curses.KEY_UP:
                if selected_idx > 0:
                    selected_idx -= 1
            elif key == curses.KEY_DOWN:
                if selected_idx < len(items) - 1:
                    selected_idx += 1
            elif key == curses.KEY_PPAGE:
                selected_idx = max(0, selected_idx - visible_lines)
            elif key == curses.KEY_NPAGE:
                selected_idx = min(len(items) - 1, selected_idx + visible_lines)
            elif key == curses.KEY_HOME:
                selected_idx = 0
            elif key == curses.KEY_END:
                selected_idx = len(items) - 1
            elif key in (10, 13, curses.KEY_ENTER):
                return items[selected_idx]['cid']
            elif key in (27, ord('q'), ord('Q')):
                return None

    try:
        return curses.wrapper(curses_main)
    except KeyboardInterrupt:
        return None

def resume_conversation(cid):
    agy_bin = shutil.which('agy') or os.path.expanduser('~/.local/bin/agy')
    if not os.path.exists(agy_bin):
        print(f"Erro: Executável 'agy' não encontrado em {agy_bin}", file=sys.stderr)
        sys.exit(1)

    print(f"\nResumindo conversa {cid} no agy...\n")
    try:
        os.execv(agy_bin, [agy_bin, '--conversation', cid])
    except Exception as e:
        print(f"Erro ao executar agy: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Navegador e seletor interativo de conversas do Antigravity CLI (agy)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('-l', '--list', '--no-interactive', dest='no_interactive', action='store_true',
                        help="Modo estático: apenas exibe a listagem tabular sem seletor interativo")
    parser.add_argument('-n', '--limit', type=int, default=None,
                        help="Limita a quantidade de conversas consultadas")
    parser.add_argument('--preview', type=str, metavar='CID',
                        help="Exibe prévia detalhada da conversa informada")
    parser.add_argument('--curses', action='store_true',
                        help="Força uso do menu curses em vez do fzf")
    parser.add_argument('--fzf', action='store_true',
                        help="Força uso do fzf")

    args = parser.parse_args()

    # If preview mode requested
    if args.preview:
        render_preview(args.preview)
        return

    items = load_conversations(limit=args.limit)
    if not items:
        print("Nenhuma conversa encontrada.")
        return

    # Non-interactive if explicitly requested or if stdout is not a TTY (e.g. pipe/redirect)
    is_interactive = sys.stdin.isatty() and sys.stdout.isatty() and not args.no_interactive

    if not is_interactive:
        print_static_table(items)
        return

    # Interactive mode: check if fzf is available
    script_path = os.path.abspath(__file__)
    fzf_available = shutil.which('fzf') is not None

    selected_cid = None
    if fzf_available and not args.curses:
        selected_cid = select_with_fzf(items, script_path)
    else:
        selected_cid = select_with_curses(items)

    if selected_cid:
        resume_conversation(selected_cid)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()
