# 🌸 Minecraft panel in Flask

A cute and simple web panel 💖 to manage a Minecraft server directly from your browser made with Python + Flask.

> this **probably** shouldn't work, but it works. - The creator of this project

## ✨ Features
- 🟢 **Start / stop the server**
- 🎮 **Active player counter** (using RCON)
- 📁 **File manager** (edit, download and send plugins or mods)
- 💾 **Option to backup** the world
- 🔍 **Logs and RCON commands** in "real time"
- 🌐 ~~integration with playit for remote access~~

## 🔜 Things to be added
- [ ] Option to delete files (?)
- [ ] Integrate with playit
- [ ] Auto backup
- [ ] Easier config
- [ ] sex


## 📦 Requirements
- Python **3.9+**
- Java (17+) installed and configured in `PATH`
- A working minecraft server (if you already have one, move it to the folder "servidor")
- RCON activated in `server.properties`

## 🚀 Instalation
Clone the repo:
```
git clone https://github.com/DarkOFC73/painel-minecraft-flask.git
cd painel-minecraft-flask
```
Create and activate a virtual env:

``python -m venv venv``

``venv\Scripts\activate`` if you use windows

``source venv/bin/activate`` if you are neglected by society (Linux/Mac)

Install the dependencies:

``pip install -r requirements.txt``

## ⚙️ Config

Create a .env file in the root folder of the repo:
```
PASSWORD=your_pass_here
SECRET_KEY=a_secret_key
JAR_NAME=server.jar (or whatever, needs to have .jar at the end btw)
RCON_PASSWORD=your_rcon_pass
RCON_PORT=25575
```


Be sure that the server.properties has these settings:
```
enable-rcon=true
rcon.password=your_rcon_pass
rcon.port=25575
```
## ▶️ Running it
in the terminal:

``python app.py``

The panel will be hosted at:

http://127.0.0.1:5000


## 📝 License

This project is licensed under the MIT License.

![Made%20with-Python-3776AB?logo=python&logoColor=white](https://img.shields.io/badge/Made%20with-Python-3776AB?logo=python&logoColor=white)
