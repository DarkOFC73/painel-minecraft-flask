
# 🌸 Minecraft Panel in Flask

A simple, fluffy 💖 and slightly miraculous ✨ web panel to manage your Minecraft server straight from your browser.  
Built with Python + Flask, duct tape, and caffeine.

[🇧🇷 Versão em português aqui!](README-ptbr.md)

> "This **probably** shouldn’t work, but it does. And better than it should."  
> — Someone who clearly didn’t test enough

---

## ✨ Features

- 🟢 **Start / Stop the server**  
  Because clicking buttons is cooler than typing in the terminal.
- 🎮 **Online player counter** (via RCON)  
  See how many friends are ignoring your server invite.
- 📁 **File manager** (edit, upload, download files)  
  *The true FTP experience… but with 80% less trauma.*
- 💾 **Complete world backup**, including all dimensions  
  Nobody wants to lose that dirt castle in the Nether.
- 🔍 **Real-time log viewer**  
  Spy on your server like the Mojang FBI.
- ⚙️ **Edit the `.env` file** directly from the panel  
  Less time in the terminal, more time breaking blocks.
- 📊 **RAM and CPU usage monitor**  
  Great for when your server is haunted by a buggy mod.
- ⌨️ **Quick RCON commands**  
  Typing `/stop` has never felt so satisfying.
- 🎨 **Totally revamped interface**  
  Prettier than Minecraft 1.20’s UI (no shade).
- 🌐 ~~Playit.gg integration for remote access~~ *(in development. maybe. someday. who knows.)*
- ✅ **Compatible with:** Forge, Fabric, Vanilla, and Paper  
  ❌ *BungeeCord and Velocity are still grounded.*

---

## 🔮 Future Features

- [ ] Delete files directly from the panel (no accidents, I swear!)
- [ ] Playit.gg integration (devs, please send help)
- [x] Automatic backups, because we make mistakes and that's ok!
- [x] Less depressing and more intuitive settings screen
- [ ] Dark mode (because our eyes are crying)
- [ ] ~~sex~~ (💀 not that kind of panel, sorry)

---

## 📦 Requirements

- Python **3.9 or higher**
- Java (version 17+) installed and in your `PATH`
- A Minecraft server (put it in the `servidor` folder)
- RCON enabled in `server.properties`

> Tip: use a lightweight `.jar` server like Paper or Vanilla (no heavy mods for testing)

---

## 🚀 Installation

Clone the repository:
```
git clone https://github.com/DarkOFC73/painel-minecraft-flask.git
cd painel-minecraft-flask
```
Create and activate a virtual environment:
```
python -m venv venv

    #Windows (running a server on Windows? really?):
    venv\Scriptsctivate

    #Linux/macOS:
    source venv/bin/activate
```
Install the dependencies:
```
pip install -r requirements.txt
```

⚙️ Configuration

Create a `.env` file with these spicy contents:
```
SECRET_KEY=super_secret_key_generatemeplspls
PASSWORD=admin
SERVER_DIR=path/to/your/server
JAR_NAME=paper.jar
PLAYIT_PATH=./playit
RCON_PASSWORD=nyan
RCON_PORT=25575
# Playit.gg Config (optional)
PLAYIT_API_KEY=your_api_key_here
PLAYIT_TUNNEL_ID=your_tunnel_id_here
PLAYIT_AGENT_PATH=./playit-agent
# Auto Backup Config
AUTO_BACKUP_ENABLED=false
AUTO_BACKUP_INTERVAL=3600
AUTO_BACKUP_KEEP=5
```
Then edit your Minecraft `server.properties`:
```
enable-rcon=true
rcon.password=your_rcon_password
rcon.port=25575
```
If you don’t enable RCON, **nothing** will work. Not the stop button. Not even your little gamer heart 💔

▶️ Running

Launch it like a pro:
```
python app.py
```
Open your browser and go to:

    http://127.0.0.1:5000

If it works, congrats. If not, congrats too — you're officially a Flask dev now. 😎

---

## 📝 License

This project is licensed under the MIT License.  
Feel free to use it, break it, fix it, and call it your own. Just don’t blame me if it breaks.

Made with Python and love 💖.
