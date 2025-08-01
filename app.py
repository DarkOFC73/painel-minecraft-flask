# painel_minecraft/app.py
from flask import Flask, render_template, request, redirect, send_file, jsonify, session, send_from_directory, url_for, abort, flash
import os, subprocess, threading, time, zipfile, socket
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from mcrcon import MCRcon
import psutil
import shutil
import socket
import json
import re
from pathlib import Path
from urllib.parse import unquote
import logging


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY") or "senha123"

SERVER_DIR = os.path.abspath("servidor") + "/"
JAR_NAME = os.getenv("JAR_NAME") or "server.jar"
PLAYIT_PATH = os.getenv("PLAYIT_PATH") or "./playit/playit-linux"
LOG_FILE = os.path.join(SERVER_DIR, "logs", "latest.log")
ALLOWED_EXTENSIONS = {"jar", "zip", "txt", "json", "cfg"}
FILE_ROOT = os.path.abspath(SERVER_DIR)
status_info = {"running": False, "players": []}
RCON_HOST = "127.0.0.1"
RCON_PASSWORD = "meowmeow"
RCON_PORT = int(os.getenv("RCON_PORT") or 25575)



# --- Funções auxiliares ---
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
            response = mcr.command("list")  # exemplo: "There are §c1§6 of a max of §a20§6 players online: Steve"
            clean_response = re.sub(r"§.", "", response)  # remove todos os códigos tipo §c, §a, etc

            if "There are" in clean_response:
                parts = clean_response.split()
                count = int(parts[2])  # agora deve ser só "1"
                return count
    except Exception as e:
        print(f"[erro RCON get_player_count]: {e}")
    return 0

def render_file_manager(subpath):
    current_path = os.path.join(SERVER_DIR, subpath)
    if not os.path.exists(current_path):
        return "Diretório não encontrado", 404

    files = []
    for name in os.listdir(current_path):
        full_path = os.path.join(current_path, name)
        files.append({
            "name": name,
            "is_dir": os.path.isdir(full_path)
        })

    # 🪜 Gera o caminho do diretório anterior
    parent_path = os.path.dirname(subpath).replace("\\", "/")
    if subpath.strip() == "":
        parent_path = None

    return render_template("file_manager.html", files=files, subpath=subpath, parent_path=parent_path)


def get_full_path(subpath):
    full = os.path.abspath(os.path.join(FILE_ROOT, subpath))
    if not full.startswith(FILE_ROOT):
        raise ValueError("Path traversal detected!")
    return full

def is_server_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        try:
            print(f"[DEBUG] Vendo processo: {proc.info['name']}, cmdline: {proc.info['cmdline']}")
            if proc.info['name'] and 'java' in proc.info['name'].lower():
                if any(JAR_NAME.lower() in str(arg).lower() for arg in proc.info['cmdline']):
                    return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return False

#initial server_state
server_state = "ligado" if is_server_running() else "desligado"

def start_server():
    global server_state
    server_state = "ligando"
    print("[DEBUG] Estado alterado para 'ligando'")

    def run():
        global server_state
        try:
            proc = subprocess.Popen(
                ["java", "-Xmx1024M", "-Xms1024M", "-jar", JAR_NAME, "nogui"],
                cwd=SERVER_DIR,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            print("[DEBUG] Processo Java iniciado, PID:", proc.pid)

            # Tenta detectar que o servidor subiu
            for i in range(20):  # tenta por até 20 segundos
                time.sleep(1)
                if is_server_running():
                    server_state = "ligado"
                    print("[DEBUG] Estado alterado para 'ligado'")
                    break
                else:
                    print(f"[DEBUG] Tentativa {i+1}: servidor ainda não detectado...")

            else:
                server_state = "desligado"
                print("[DEBUG] Não foi possível detectar o servidor em 20s")

            proc.wait()
            print("[DEBUG] Processo Java terminou")

        except Exception as e:
            print(f"[start_server error]: {e}")
            server_state = "desligado"
        finally:
            server_state = "desligado"
            print("[DEBUG] Estado alterado para 'desligado' no finally")

    threading.Thread(target=run, daemon=True).start()



def stop_server():
    global server_state
    server_state = "desligando"
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            name = proc.info['name']
            cmdline = proc.info['cmdline']
            if isinstance(cmdline, list):
                joined_cmd = ' '.join(cmdline).lower()
            else:
                joined_cmd = ''
            if name and 'java' in name.lower() and JAR_NAME.lower() in joined_cmd:
                proc.terminate()
                proc.wait(timeout=10)
        except Exception as e:
            print(f"[stop_server] erro: {e}")
    server_state = "desligado"

def get_satus():
    return status_info

def backup_world():
    backup_path = os.path.join(SERVER_DIR, "world_backup.zip")
    with zipfile.ZipFile(backup_path, 'w') as z:
        for root, dirs, files in os.walk(os.path.join(SERVER_DIR, "world")):
            for file in files:
                abs_path = os.path.join(root, file)
                z.write(abs_path, os.path.relpath(abs_path, SERVER_DIR))
    return backup_path

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_playit_status():
    try:
        result = subprocess.check_output(["pgrep", "-af", "playit"])
        return "Online" if b"playit" in result else "Offline"
    except:
        return "Offline"

def list_players():
    return status_info["players"]

def read_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            return f.read()
    return "Sem logs ainda, nya~"

def run_command(cmd):
    # Supondo que o servidor esteja rodando em screen ou você queira mandar via stdin (precisa ajustar para seu caso)
    input_file = os.path.join(SERVER_DIR, "console_input.txt")
    with open(input_file, "a") as f:
        f.write(cmd + "\n")
    return True

# --- Rotas ---
@app.route("/status_json")
def status_json():
    global server_state
    if is_server_running():
        if server_state != "ligando":
            server_state = "ligado"
    else:
        if server_state != "desligando":
            server_state = "desligado"

    return jsonify({
        "status": server_state,
        "players": get_player_count() if server_state == "ligado" else 0
    })

@app.route("/stream_logs")
def stream_logs():
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return jsonify(lines[-50:])  # Retorna as últimas 50 linhas
    except Exception as e:
        return jsonify([f"[Erro ao ler log]: {e}"])

@app.route("/send_command", methods=["POST"])
def send_command():
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
    relative_path = request.args.get("path")
    if not relative_path:
        abort(404)

    file_path = os.path.abspath(os.path.join(SERVER_DIR, relative_path.lstrip("/\\")))

    if not file_path.startswith(os.path.abspath(SERVER_DIR)) or not os.path.isfile(file_path):
        abort(404)

    parent_path = str(Path(file_path).parent)

    if request.method == "POST":
        content = request.form.get("content", "")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            flash("Arquivo salvo com sucesso! (≧◡≦) ♡")
        except Exception as e:
            flash(f"Erro ao salvar arquivo: {e}")
        return redirect(url_for("file_manager", path=os.path.dirname(file_path)))

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    return render_template("edit_file.html", file_path=file_path, parent_path=parent_path, content=content)


@app.route("/files/", defaults={"path": ""})
@app.route("/files/<path:path>")
def file_manager(path):
    safe_base = os.path.abspath(SERVER_DIR)
    normalized_path = os.path.normpath(unquote(path))
    full_path = os.path.abspath(os.path.join(safe_base, normalized_path))

    # 🚨 Bloqueia acesso fora do SERVER_DIR
    if not full_path.startswith(safe_base):
        abort(403)  # Acesso proibido!

    if not os.path.exists(full_path):
        abort(404)

    entries = []
    for entry in os.listdir(full_path):
        entry_path = os.path.join(normalized_path, entry)
        entries.append({
            "name": entry,
            "path": entry_path.replace("\\", "/"),
            "is_dir": os.path.isdir(os.path.join(full_path, entry))
        })

    # 🪜 Garante que não volte além do root
    parent_path = os.path.dirname(normalized_path).replace("\\", "/") if normalized_path else None

    return render_template("file_manager.html",
                           files=entries,
                           current_path=normalized_path,
                           parent_path=parent_path,
                           SERVER_DIR=safe_base)


@app.route("/download/<path:subpath>")
def download_file(subpath):
    abs_path = get_full_path(subpath)
    dir_name = os.path.dirname(abs_path)
    filename = os.path.basename(abs_path)
    return send_from_directory(dir_name, filename, as_attachment=True)

@app.route("/view/<path:subpath>")
def view_file(subpath):
    try:
        abs_path = get_full_path(subpath)
        with open(abs_path, encoding="utf-8") as f:
            content = f.read()
        return render_template("view_file.html", content=content, path=subpath)
    except Exception as e:
        return f"Erro ao ler o arquivo: {e}", 500

@app.route("/delete/<path:subpath>", methods=["POST"])
def delete_file(subpath):
    try:
        abs_path = get_full_path(subpath)
        if os.path.isfile(abs_path):
            os.remove(abs_path)
        elif os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        return redirect(url_for("file_manager", subpath=os.path.dirname(subpath)))
    except Exception as e:
        return f"Erro ao excluir: {e}", 500

@app.route("/upload/<path:subpath>", methods=["POST"])
def upload_file(subpath):
    try:
        file = request.files["file"]
        filename = secure_filename(file.filename)
        upload_path = get_full_path(os.path.join(subpath, filename))
        file.save(upload_path)
        return redirect(url_for("file_manager", subpath=subpath))
    except Exception as e:
        return f"Erro ao enviar: {e}", 500

@app.route("/get_logs")
def get_logs():
    try:
        with open(os.path.join(SERVER_DIR, "logs/latest.log"), "r", encoding="utf-8") as f:
            content = f.read()
        return content
    except FileNotFoundError:
        return "Log file not found."

@app.route("/")
def index():
    server_online = is_server_running()
    player_count = get_player_count() if server_online else 0
    return render_template("index.html",server_online=server_online, server_state=server_state, player_count=player_count)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["password"] == os.getenv("PASSWORD"):
            session["auth"] = True
            return redirect("/")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/start', methods=['POST'])
def start():
    if not is_server_running():
        start_server()
        return "Servidor iniciado com sucesso! OwO"
    return "Servidor já está rodando! UwU"
    return redirect(url_for('index'))

@app.route('/stop', methods=['POST'])
def stop():
    stop_server()
    return redirect("/")
    return redirect(url_for('index'))

@app.route('/status', methods=['GET'])
def status():
    return jsonify({
        "status": "online" if is_server_running() else "offline",
        "player_count": get_player_count()
    })

@app.route("/backup")
def backup():
    path = backup_world()
    return send_file(path, as_attachment=True)

@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return "No file part"
    
    file = request.files["file"]
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        # Usa a função nova aqui UwU
        plugin_dir = os.path.join(SERVER_DIR, "plugins/update" if is_server_running() else "plugins")
        os.makedirs(plugin_dir, exist_ok=True)

        file.save(os.path.join(plugin_dir, filename))
        return redirect("/")
    
    return "Invalid file"


@app.route("/console", methods=["POST"])
def console():
    cmd = request.form.get("command")
    if cmd:
        try:
            with MCRcon("127.0.0.1", "meowmeow", port=25575) as mcr:
                resp = mcr.command(cmd)
                return f"<pre>{resp}</pre>"
        except Exception as e:
            return f"Erro ao enviar comando: {e}"
    return "Nenhum comando enviado."

@app.route("/files")
def files():
    files = os.listdir(SERVER_DIR)
    return jsonify(files)

@app.route("/logs")
def logs():
    return render_template("logs.html", content=read_logs())

@app.route("/send", methods=["POST"])
def send():
    cmd = request.form.get("command")
    if cmd:
        run_command(cmd)
    return redirect("/logs")

@app.route("/refresh", methods=["GET"])
def refresh_status():
    return redirect(url_for("index"))


if __name__ == "__main__":
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)

    app.run(host="0.0.0.0", port=5000)
