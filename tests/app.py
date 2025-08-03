# painel_minecraft/app.py
from flask import Flask, render_template, request, redirect, send_file, jsonify, session, send_from_directory, url_for, abort, flash
import os, subprocess, threading, time, zipfile, socket
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from mcrcon import MCRcon
import psutil
import shutil
import json
import re
from pathlib import Path
from urllib.parse import unquote
import logging
import requests
import schedule
import atexit
import glob
import platform
import secrets
import string

# Configuração de logging para reduzir os debugs
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

load_dotenv()

def get_env_var(name, default=None, required=False):
    """Obtém variável de ambiente com opção de valor padrão ou obrigatório"""
    value = os.getenv(name, default)
    if required and not value:
        raise SystemExit(f"[ERRO] Variável de ambiente obrigatória '{name}' não definida no .env!")
    return value

# Configurações essenciais (obrigatórias)
app = Flask(__name__)
app.secret_key = get_env_var("SECRET_KEY", required=True)
PASSWORD = get_env_var("PASSWORD", required=True)
RCON_PASSWORD = get_env_var("RCON_PASSWORD", required=True)
RCON_PORT = int(get_env_var("RCON_PORT", 25575))

# Configurações opcionais com valores padrão
SERVER_DIR = os.path.abspath(get_env_var("SERVER_DIR", "servidor")) + "/"
JAR_NAME = get_env_var("JAR_NAME", "server.jar")
PLAYIT_PATH = get_env_var("PLAYIT_PATH", "./playit-agent")
LOG_FILE = os.path.join(SERVER_DIR, "logs", "latest.log")
ALLOWED_EXTENSIONS = {"jar", "zip", "txt", "json", "cfg", "yml", "yaml", "dat", "mcfunction", " properties", "toml", "conf"}
FILE_ROOT = os.path.abspath(SERVER_DIR)
status_info = {"running": False, "players": []}
RCON_HOST = "127.0.0.1"

# Configurações do Playit.gg (opcionais)
PLAYIT_API_KEY = os.getenv("PLAYIT_API_KEY", "")
PLAYIT_TUNNEL_ID = os.getenv("PLAYIT_TUNNEL_ID", "")
PLAYIT_AGENT_PATH = os.getenv("PLAYIT_AGENT_PATH", "./playit-agent")

# Configurações de Backup Automático (opcionais)
AUTO_BACKUP_ENABLED = os.getenv("AUTO_BACKUP_ENABLED", "false").lower() == "true"
AUTO_BACKUP_INTERVAL = int(os.getenv("AUTO_BACKUP_INTERVAL", "3600"))  # segundos
AUTO_BACKUP_KEEP = int(os.getenv("AUTO_BACKUP_KEEP", "5"))

# Variável global para o job do backup
backup_job = None

# --- Funções auxiliares ---
def read_env_file():
    """Lê o arquivo .env e retorna as configurações"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    env_vars = {}
    
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove aspas se existirem
                    value = value.strip('"\'')
                    env_vars[key.strip()] = value
    
    return env_vars

def write_env_file(env_vars):
    """Escreve as configurações no arquivo .env"""
    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    
    # Template do arquivo .env com comentários
    env_template = """# Configurações do Painel Minecraft
SECRET_KEY={SECRET_KEY}
PASSWORD={PASSWORD}
SERVER_DIR={SERVER_DIR}
JAR_NAME={JAR_NAME}
PLAYIT_PATH={PLAYIT_PATH}
RCON_PASSWORD={RCON_PASSWORD}
RCON_PORT={RCON_PORT}
# Configurações do Playit.gg (opcionais)
PLAYIT_API_KEY={PLAYIT_API_KEY}
PLAYIT_TUNNEL_ID={PLAYIT_TUNNEL_ID}
PLAYIT_AGENT_PATH={PLAYIT_AGENT_PATH}
# Configurações de Backup Automático
AUTO_BACKUP_ENABLED={AUTO_BACKUP_ENABLED}
AUTO_BACKUP_INTERVAL={AUTO_BACKUP_INTERVAL}
AUTO_BACKUP_KEEP={AUTO_BACKUP_KEEP}
"""

    # Preencher valores padrão se não existirem
    defaults = {
        'SECRET_KEY': env_vars.get('SECRET_KEY', 'sua_chave_secreta_aqui'),
        'PASSWORD': env_vars.get('PASSWORD', 'sua_senha_aqui'),
        'SERVER_DIR': env_vars.get('SERVER_DIR', '/caminho/para/servidor'),
        'JAR_NAME': env_vars.get('JAR_NAME', 'server.jar'),
        'PLAYIT_PATH': env_vars.get('PLAYIT_PATH', './playit'),
        'RCON_PASSWORD': env_vars.get('RCON_PASSWORD', 'senha_rcon'),
        'RCON_PORT': env_vars.get('RCON_PORT', '25575'),
        'PLAYIT_API_KEY': env_vars.get('PLAYIT_API_KEY', ''),
        'PLAYIT_TUNNEL_ID': env_vars.get('PLAYIT_TUNNEL_ID', ''),
        'PLAYIT_AGENT_PATH': env_vars.get('PLAYIT_AGENT_PATH', './playit-agent'),
        'AUTO_BACKUP_ENABLED': env_vars.get('AUTO_BACKUP_ENABLED', 'false'),
        'AUTO_BACKUP_INTERVAL': env_vars.get('AUTO_BACKUP_INTERVAL', '3600'),
        'AUTO_BACKUP_KEEP': env_vars.get('AUTO_BACKUP_KEEP', '5')
    }
    
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write(env_template.format(**defaults))

def send_rcon_command(command):
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(command)
        return response
    except Exception as e:
        return f"Erro ao enviar comando: {e}"

def check_server_status(host='127.0.0.1', port=25565):
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except Exception:
        return False

def get_player_count():
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=int(RCON_PORT)) as mcr:
            response = mcr.command("list")  
            clean_response = re.sub(r"§.", "", response)  
            if "There are" in clean_response:
                parts = clean_response.split()
                count = int(parts[2])  
                return count
    except Exception as e:
        pass  # Removido o print de erro para não poluir o painel
    return 0

def get_full_path(subpath):
    full = os.path.abspath(os.path.join(FILE_ROOT, subpath))
    if not full.startswith(FILE_ROOT):
        raise ValueError("Path traversal detected!")
    return full

def is_server_running():
    """Detecta se o servidor está rodando com suporte a Fabric, Forge e Vanilla"""
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            if proc.info['name'] and 'java' in proc.info['name'].lower():
                cmdline = ' '.join(proc.info['cmdline']).lower()
                # Verifica se é o servidor correto pelo diretório e JAR
                if (os.path.abspath(SERVER_DIR).lower() in cmdline and 
                    JAR_NAME.lower() in cmdline):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

server_state = "ligado" if is_server_running() else "desligado"

def start_server():
    """Inicia o servidor com suporte a diferentes tipos (Fabric, Forge, Vanilla)"""
    global server_state
    server_state = "ligando"
    
    def run():
        global server_state
        try:
            # Detectar tipo de servidor para comando apropriado
            jar_path = os.path.join(SERVER_DIR, JAR_NAME)
            
            # Comando base
            cmd = ["java", "-Xmx2048M", "-Xms2048M"]
            
            # Adicionar flags específicas conforme o tipo de servidor
            if "fabric" in JAR_NAME.lower():
                cmd.extend(["-jar", JAR_NAME, "nogui"])
            elif "forge" in JAR_NAME.lower():
                cmd.extend(["-jar", JAR_NAME, "--nogui"])
            else:  # Vanilla ou outros
                cmd.extend(["-jar", JAR_NAME, "nogui"])
            
            proc = subprocess.Popen(
                cmd,
                cwd=SERVER_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            for i in range(20):  
                time.sleep(1)
                if is_server_running():
                    server_state = "ligado"
                    break
                else:
                    pass  # Removido o print de debug
            else:
                server_state = "desligado"
            proc.wait()
        except Exception as e:
            server_state = "desligado"
        finally:
            server_state = "desligado"
    
    threading.Thread(target=run, daemon=True).start()

# socorro
def stop_server():
    """Para o servidor identificando o processo específico com suporte a diferentes tipos"""
    global server_state
    server_state = "desligando"
    
    # Primeiro tenta parar via RCON
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            mcr.command("stop")
        # Espera um pouco para o servidor parar gracefulmente
        time.sleep(5)
    except:
        pass  # Se RCON falhar, continua com kill
    
    # Encontra o processo específico do servidor
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            # Verifica se é um processo Java com o JAR correto no diretório correto
            if (proc.info['name'] and 'java' in proc.info['name'].lower() and 
                any(JAR_NAME.lower() in str(arg).lower() for arg in proc.info['cmdline']) and
                str(proc.info['cwd']).lower() == os.path.abspath(SERVER_DIR).lower()):
                
                # Tenta parar gracefulmente primeiro
                proc.terminate()
                try:
                    proc.wait(timeout=10)
                except psutil.TimeoutExpired:
                    # Se não parar, força
                    proc.kill()
                    proc.wait()
                break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    server_state = "desligado"

def backup_world():
    """Realiza backup do mundo do servidor (suporte a múltiplos mundos)"""
    try:
        timestamp = time.strftime("%Y%m%d-%H%M%S")
        backup_filename = f"world_backup_{timestamp}.zip"
        backup_path = os.path.join(SERVER_DIR, backup_filename)
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as z:
            # Encontra todas as pastas que começam com "world"
            world_dirs = glob.glob(os.path.join(SERVER_DIR, "world*"))
            for world_dir in world_dirs:
                if os.path.isdir(world_dir):
                    world_name = os.path.basename(world_dir)
                    # Ignora pastas temporárias ou de backup
                    if not world_name.endswith(('_backup', '_tmp', '_old')):
                        for root, dirs, files in os.walk(world_dir):
                            for file in files:
                                abs_path = os.path.join(root, file)
                                arc_path = os.path.relpath(abs_path, SERVER_DIR)
                                z.write(abs_path, arc_path)
        return backup_path
    except Exception as e:
        print(f"[ERRO] Backup falhou: {e}")
        return None

def cleanup_old_backups():
    """Remove backups antigos mantendo apenas os mais recentes"""
    try:
        backup_pattern = os.path.join(SERVER_DIR, "world_backup_*.zip")
        backups = glob.glob(backup_pattern)
        backups.sort(key=os.path.getmtime, reverse=True)
        
        for old_backup in backups[AUTO_BACKUP_KEEP:]:
            try:
                os.remove(old_backup)
                print(f"[BACKUP] Backup antigo removido: {os.path.basename(old_backup)}")
            except Exception as e:
                print(f"[ERRO] Falha ao remover backup {old_backup}: {e}")
    except Exception as e:
        print(f"[ERRO] Falha na limpeza de backups: {e}")

def automated_backup():
    """Função que executa o backup automático"""
    if not AUTO_BACKUP_ENABLED:
        return
        
    print("[BACKUP] Iniciando backup automático...")
    backup_path = backup_world()
    if backup_path:
        print(f"[BACKUP] Backup concluído: {os.path.basename(backup_path)}")
        cleanup_old_backups()
    else:
        print("[ERRO] Falha no backup automático")

def start_backup_scheduler():
    """Inicia o agendador de backups automáticos"""
    global backup_job
    
    if AUTO_BACKUP_ENABLED and AUTO_BACKUP_INTERVAL > 0:
        # Cancelar job anterior se existir
        if backup_job:
            schedule.cancel_job(backup_job)
        
        # Agendar novo backup
        backup_job = schedule.every(AUTO_BACKUP_INTERVAL).seconds.do(automated_backup)
        
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        # Rodar em thread separada
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        print(f"[BACKUP] Agendador iniciado - Backup a cada {AUTO_BACKUP_INTERVAL} segundos")
    else:
        print("[BACKUP] Backup automático desativado")

def allowed_file(filename):
    """Verifica se o arquivo é permitido e faz validações adicionais"""
    # Verificação básica de extensão
    if not '.' in filename:
        return False
        
    ext = filename.rsplit('.', 1)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    
    # Validações adicionais para arquivos JAR
    if ext == 'jar':
        # Limita tamanho de JARs para 100MB
        # Esta verificação seria feita no upload, mas aqui garantimos segurança
        pass
    
    return True

# Funções da API do Playit.gg
def get_playit_api_headers():
    """Retorna os headers necessários para a API do Playit.gg"""
    return {
        "Authorization": f"Bearer {PLAYIT_API_KEY}",
        "Content-Type": "application/json"
    }

def get_playit_account_info():
    """Obtém informações da conta Playit.gg"""
    if not PLAYIT_API_KEY:
        return None
    
    try:
        headers = get_playit_api_headers()
        response = requests.get("https://api.playit.gg/account", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        print(f"[Playit API] Erro ao obter info da conta: {e}")
        return None

def get_playit_tunnels():
    """Obtém a lista de túneis do Playit.gg"""
    if not PLAYIT_API_KEY:
        return []
    
    try:
        headers = get_playit_api_headers()
        response = requests.get("https://api.playit.gg/tunnels", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception as e:
        print(f"[Playit API] Erro ao obter túneis: {e}")
        return []

def get_playit_tunnel_info(tunnel_id):
    """Obtém informações de um túnel específico"""
    if not PLAYIT_API_KEY or not tunnel_id:
        return None
    
    try:
        headers = get_playit_api_headers()
        response = requests.get(f"https://api.playit.gg/tunnels/{tunnel_id}", headers=headers, timeout=5)
        if response.status_code == 200:
            return response.json().get("data")
        return None
    except Exception as e:
        print(f"[Playit API] Erro ao obter info do túnel {tunnel_id}: {e}")
        return None

# Funções do agente local do Playit.gg
def get_playit_agent_status():
    """Verifica se o agente do Playit está rodando localmente (multiplataforma)"""
    try:
        sistema = platform.system().lower()
        if sistema == "windows":
            # No Windows, usa tasklist
            result = subprocess.check_output(["tasklist"], stderr=subprocess.DEVNULL)
            return "Online" if b"playit" in result.lower() else "Offline"
        else:
            # No Linux/Mac, usa pgrep
            result = subprocess.check_output(["pgrep", "-af", "playit"], stderr=subprocess.DEVNULL)
            return "Online" if b"playit" in result else "Offline"
    except:
        return "Offline"

def start_playit_agent():
    """Inicia o agente do Playit.gg"""
    try:
        if not os.path.exists(PLAYIT_AGENT_PATH):
            return False, "Agente do Playit não encontrado"
        subprocess.Popen([PLAYIT_AGENT_PATH], cwd=os.path.dirname(PLAYIT_AGENT_PATH))
        return True, "Playit.gg iniciado com sucesso"
    except Exception as e:
        return False, f"Erro ao iniciar Playit: {str(e)}"

def stop_playit_agent():
    """Para o agente do Playit.gg"""
    try:
        sistema = platform.system().lower()
        if sistema == "windows":
            # No Windows, usa taskkill
            subprocess.run(["taskkill", "/f", "/im", "playit*.exe"], stderr=subprocess.DEVNULL)
        else:
            # No Linux/Mac, usa pkill
            subprocess.run(["pkill", "-f", "playit"], stderr=subprocess.DEVNULL)
        return True, "Playit.gg parado com sucesso"
    except Exception as e:
        return False, f"Erro ao parar Playit: {str(e)}"

def list_players():
    return status_info["players"]

def read_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    return "Sem logs ainda, nya~"

def run_command(cmd):
    input_file = os.path.join(SERVER_DIR, "console_input.txt")
    with open(input_file, "a") as f:
        f.write(cmd + "\n")
    return True

# --- Rotas ---
@app.route('/config', methods=['GET', 'POST'])
def config():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        env_vars = {}
        for key in request.form:
            if request.form[key].strip():  # Só salvar se não estiver vazio
                env_vars[key] = request.form[key].strip()
        
        try:
            write_env_file(env_vars)
            flash("Configurações salvas com sucesso! Reinicie a aplicação para aplicar as mudanças.", "success")
        except Exception as e:
            flash(f"Erro ao salvar configurações: {e}", "error")
        
        return redirect(url_for('config'))
    
    current_env = read_env_file()
    
    return render_template('config.html', env_vars=current_env)

@app.route('/config/generate_secret', methods=['POST'])
def generate_secret():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    secret_key = ''.join(secrets.choice(string.ascii_letters + string.digits + '!@#$%^&*') for _ in range(32))
    
    return jsonify({'secret_key': secret_key})

@app.route('/config/validate', methods=['POST']) #nn remove pls
def validate_config():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    validation_results = {}
    
    server_dir = request.json.get('SERVER_DIR', '')
    if server_dir:
        validation_results['SERVER_DIR'] = {
            'exists': os.path.exists(server_dir),
            'writable': os.access(server_dir, os.W_OK) if os.path.exists(server_dir) else False
        }

    jar_name = request.json.get('JAR_NAME', '')
    if jar_name and server_dir:
        jar_path = os.path.join(server_dir, jar_name)
        validation_results['JAR_NAME'] = {
            'exists': os.path.exists(jar_path),
            'is_jar': jar_name.endswith('.jar')
        }

    playit_path = request.json.get('PLAYIT_PATH', '')
    if playit_path:
        validation_results['PLAYIT_PATH'] = {
            'exists': os.path.exists(playit_path),
            'executable': os.access(playit_path, os.X_OK) if os.path.exists(playit_path) else False
        }
    
    rcon_port = request.json.get('RCON_PORT', '')
    if rcon_port:
        try:
            port = int(rcon_port)
            validation_results['RCON_PORT'] = {
                'valid_range': 1 <= port <= 65535
            }
        except ValueError:
            validation_results['RCON_PORT'] = {
                'valid_range': False
            }
    
    return jsonify(validation_results)

@app.route("/status_json")
def status_json():
    global server_state
    if is_server_running():
        if server_state != "ligando":
            server_state = "ligado"
    else:
        if server_state != "desligando":
            server_state = "desligado"
    
    # Verificar status do Playit
    playit_agent_status = get_playit_agent_status()
    
    # Obter informações da API do Playit (se configurada)
    playit_tunnel_info = None
    if PLAYIT_API_KEY and PLAYIT_TUNNEL_ID:
        playit_tunnel_info = get_playit_tunnel_info(PLAYIT_TUNNEL_ID)
    
    return jsonify({
        "status": server_state,
        "players": get_player_count() if server_state == "ligado" else 0,
        "playit_agent_status": playit_agent_status,
        "playit_tunnel_info": playit_tunnel_info
    })

@app.route("/stream_logs")
def stream_logs():
    try:
        with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        return jsonify(lines[-50:])
    except Exception as e:
        return jsonify([f"[Erro ao ler log]: {e}"])

@app.route("/send_command", methods=["POST"])
def send_command():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    command = request.form.get("command", "")
    if command.strip() == "":
        flash("Comando vazio, nyan! (>_<)")
        return redirect(url_for("logs"))
    output = send_rcon_command(command)
    flash(f"Resultado: {output}")
    return redirect(url_for("logs"))

@app.route("/files")
def redirect_files():
    return redirect("/files/")

@app.route("/edit", methods=["GET", "POST"])
def edit_file():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    relative_path = request.args.get("path")
    if not relative_path:
        abort(404)
    
    file_path = os.path.abspath(os.path.join(SERVER_DIR, relative_path.lstrip("/\\")))
    if not file_path.startswith(os.path.abspath(SERVER_DIR)) or not os.path.isfile(file_path):
        abort(404)
    
    parent_dir_relative = os.path.dirname(relative_path) if os.path.dirname(relative_path) != "." else ""
    
    if request.method == "POST":
        content = request.form.get("content", "")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            flash("Arquivo salvo com sucesso! (≧◡≦) ♡")
        except Exception as e:
            flash(f"Erro ao salvar arquivo: {e}")
        
        return redirect(url_for("file_manager", path=parent_dir_relative))
    
    
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    return render_template("edit_file.html", 
                          file_path=relative_path,  
                          parent_path=parent_dir_relative, 
                          content=content)

@app.route("/files/", defaults={"path": ""})
@app.route("/files/<path:path>")
def file_manager(path):
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    safe_base = os.path.abspath(SERVER_DIR)
    normalized_path = os.path.normpath(unquote(path))
    full_path = os.path.abspath(os.path.join(safe_base, normalized_path))
    if not full_path.startswith(safe_base):
        abort(403)
    if not os.path.exists(full_path):
        abort(404)
    entries = []
    for entry in os.listdir(full_path):
        entry_path = os.path.join(normalized_path, entry)
        entries.append({
            "name": entry,
            "path": entry_path.replace("\\", "/"),
            "is_dir": os.path.isdir(os.path.join(full_path, entry)),
            "size": os.path.getsize(os.path.join(full_path, entry)) if not os.path.isdir(os.path.join(full_path, entry)) else 0
        })
    parent_path = os.path.dirname(normalized_path).replace("\\", "/") if normalized_path else None
    return render_template("file_manager.html",
                           files=entries,
                           current_path=normalized_path,
                           parent_path=parent_path,
                           SERVER_DIR=safe_base)

@app.route("/download/<path:subpath>")
def download_file(subpath):
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    try:
        abs_path = get_full_path(subpath)
        dir_name = os.path.dirname(abs_path)
        filename = os.path.basename(abs_path)
        return send_from_directory(dir_name, filename, as_attachment=True)
    except Exception as e:
        flash(f"Erro ao baixar arquivo: {e}")
        return redirect(url_for('file_manager', path=os.path.dirname(subpath)))

@app.route("/view/<path:subpath>")
def view_file(subpath):
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    try:
        abs_path = get_full_path(subpath)
        with open(abs_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return render_template("view_file.html", content=content, path=subpath)
    except Exception as e:
        return f"Erro ao ler o arquivo: {e}", 500

@app.route("/delete/<path:subpath>", methods=["POST"])
def delete_file(subpath):
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    try:
        abs_path = get_full_path(subpath)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
            flash(f"Arquivo {os.path.basename(subpath)} deletado com sucesso!", "success")
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
            flash(f"Pasta {os.path.basename(subpath)} deletada com sucesso!", "success")
        return redirect(url_for("file_manager", path=os.path.dirname(subpath)))
    except Exception as e:
        flash(f"Erro ao excluir: {e}", "error")
        return redirect(url_for("file_manager", path=os.path.dirname(subpath)))

@app.route("/upload/<path:subpath>", methods=["POST"])
def upload_file(subpath):
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    try:
        file = request.files["file"]
        if file and file.filename:
            filename = secure_filename(file.filename)
            upload_path = get_full_path(os.path.join(subpath, filename))
            
            # Validação adicional para arquivos JAR
            if filename.lower().endswith('.jar'):
                # Verifica o tamanho do arquivo (limitar a 100MB)
                file.seek(0, os.SEEK_END)
                size = file.tell()
                file.seek(0)
                if size > 100 * 1024 * 1024:  # 100MB
                    flash("Arquivo JAR muito grande! Limite: 100MB", "error")
                    return redirect(url_for("file_manager", path=subpath))
            
            file.save(upload_path)
            flash(f"Arquivo {filename} enviado com sucesso!", "success")
        return redirect(url_for("file_manager", path=subpath))
    except Exception as e:
        flash(f"Erro ao enviar: {e}", "error")
        return redirect(url_for("file_manager", path=subpath))

@app.route("/get_logs")
def get_logs():
    try:
        with open(os.path.join(SERVER_DIR, "logs/latest.log"), "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "Log file not found."

@app.route("/")
def index():
    server_online = is_server_running()
    player_count = get_player_count() if server_online else 0
    playit_agent_status = get_playit_agent_status()
    
    # Informações da API do Playit (se configurada)
    playit_account_info = None
    playit_tunnel_info = None
    playit_tunnels = []
    
    if PLAYIT_API_KEY:
        playit_account_info = get_playit_account_info()
        playit_tunnels = get_playit_tunnels()
        if PLAYIT_TUNNEL_ID:
            playit_tunnel_info = get_playit_tunnel_info(PLAYIT_TUNNEL_ID)
    
    return render_template("index.html",
                          server_online=server_online, 
                          server_state=server_state, 
                          player_count=player_count,
                          playit_agent_status=playit_agent_status,
                          playit_account_info=playit_account_info,
                          playit_tunnel_info=playit_tunnel_info,
                          playit_tunnels=playit_tunnels,
                          auto_backup_enabled=AUTO_BACKUP_ENABLED,
                          auto_backup_interval=AUTO_BACKUP_INTERVAL,
                          auto_backup_keep=AUTO_BACKUP_KEEP)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == PASSWORD:
            session["auth"] = True
            flash("Login realizado com sucesso!", "success")
            return redirect("/")
        else:
            flash("Senha incorreta!", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("Você foi desconectado!", "info")
    return redirect("/login")

@app.route('/start', methods=['POST'])
def start():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    if not is_server_running():
        start_server()
        flash("Servidor iniciado com sucesso! OwO", "success")
    else:
        flash("Servidor já está rodando! UwU", "info")
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    stop_server()
    flash("Servidor parado com sucesso!", "success")
    return redirect(url_for('index'))

@app.route('/status', methods=['GET'])
def status():
    playit_agent_status = get_playit_agent_status()
    
    # Informações da API do Playit (se configurada)
    playit_tunnel_info = None
    if PLAYIT_API_KEY and PLAYIT_TUNNEL_ID:
        playit_tunnel_info = get_playit_tunnel_info(PLAYIT_TUNNEL_ID)
    
    return jsonify({
        "status": "online" if is_server_running() else "offline",
        "player_count": get_player_count(),
        "playit_agent_status": playit_agent_status,
        "playit_tunnel_info": playit_tunnel_info
    })

@app.route("/backup")
def backup():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    path = backup_world()
    if path and os.path.exists(path):
        flash("Backup realizado com sucesso!", "success")
        cleanup_old_backups()
        return send_file(path, as_attachment=True)
    else:
        flash("Erro ao realizar backup!", "error")
        return redirect(url_for('index'))

@app.route("/upload", methods=["POST"])
def upload():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    if "file" not in request.files:
        flash("Nenhum arquivo selecionado!", "error")
        return redirect("/")
    file = request.files["file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        
        # Validação adicional para arquivos JAR
        if filename.lower().endswith('.jar'):
            # Verifica o tamanho do arquivo (limitar a 100MB)
            file.seek(0, os.SEEK_END)
            size = file.tell()
            file.seek(0)
            if size > 100 * 1024 * 1024:  # 100MB
                flash("Arquivo JAR muito grande! Limite: 100MB", "error")
                return redirect("/")
        
        plugin_dir = os.path.join(SERVER_DIR, "plugins/update" if is_server_running() else "plugins")
        os.makedirs(plugin_dir, exist_ok=True)
        file.save(os.path.join(plugin_dir, filename))
        flash(f"Arquivo {filename} enviado com sucesso!", "success")
        return redirect("/")
    else:
        flash("Tipo de arquivo não permitido!", "error")
        return redirect("/")

@app.route("/console", methods=["POST"])
def console():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    cmd = request.form.get("command")
    if cmd:
        try:
            with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
                resp = mcr.command(cmd)
                return f"<pre>{resp}</pre>"
        except Exception as e:
            return f"Erro ao enviar comando: {e}"
    return "Nenhum comando enviado."

@app.route("/logs")
def logs():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    return render_template("logs.html", content=read_logs())

@app.route("/send", methods=["POST"])
def send():
    if not session.get('auth'):
        return redirect(url_for('login'))
        
    cmd = request.form.get("command")
    if cmd:
        run_command(cmd)
        flash("Comando enviado para o console!", "success")
    return redirect("/logs")

# --- Rotas para Playit.gg ---
@app.route('/playit/start', methods=['POST'])
def start_playit_route():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    success, message = start_playit_agent()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('index'))

@app.route('/playit/stop', methods=['POST'])
def stop_playit_route():
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    success, message = stop_playit_agent()
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    return redirect(url_for('index'))

@app.route('/playit/status')
def playit_status_api():
    status = get_playit_agent_status()
    return jsonify({"status": status})

# --- Rotas para Backup Automático ---
@app.route('/backup/auto/run', methods=['POST'])
def manual_auto_backup():
    """Rota para executar backup manual através do backup automático"""
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    try:
        backup_path = backup_world()
        if backup_path:
            cleanup_old_backups()
            flash("Backup automático executado com sucesso!", "success")
        else:
            flash("Erro ao executar backup automático", "error")
    except Exception as e:
        flash(f"Erro ao executar backup: {e}", "error")
    
    return redirect(url_for('index'))

@app.route('/backup/auto/toggle', methods=['POST'])
def backup_auto_toggle():
    """Rota para ativar/desativar backup automático"""
    if not session.get('auth'):
        return redirect(url_for('login'))
    
    global AUTO_BACKUP_ENABLED
    AUTO_BACKUP_ENABLED = not AUTO_BACKUP_ENABLED
    
    # Reiniciar scheduler
    start_backup_scheduler()
    
    status = "ativado" if AUTO_BACKUP_ENABLED else "desativado"
    flash(f"Backup automático {status} com sucesso!", "success")
    
    return redirect(url_for('index'))

if __name__ == "__main__":
    # Iniciar agendador de backups quando a aplicação começar
    start_backup_scheduler()
    
    # Registrar função para limpar ao sair
    atexit.register(lambda: print("Aplicação encerrada"))
    
    app.run(host="0.0.0.0", port=5000, debug=False)
    # teste ae, se isso funcionar de primeira, hoje tu entra na chapa, senhor dark
