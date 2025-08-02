# 🌸 Painel Minecraft em Flask

Um painel web simples e fofinho 💖 para gerenciar um servidor de Minecraft diretamente do navegador, feito com Python + Flask.

[🇺🇸 En-US translation here!](README-en.md)

> isso **provavelmente** não deveria funcionar, mas funciona. - O criador desse projeto

## ✨ Funcionalidades
- 🟢 **Iniciar / Parar servidor**
- 🎮 **Contador de jogadores online** (via RCON)
- 📁 **Gerenciador de arquivos** (editar, baixar, enviar arquivos)
- 💾 **Opção para backup** do mundo
- 🔍 **Visualização de logs** em "tempo real"
- 🌐 ~~Integração com playit.gg para acesso remoto~~

## 🔜 Coisas a serem adicionadas
- [ ] Opção pra deletar arquivos (?)
- [ ] Integração com Playit.gg
- [ ] Backup automatico
- [ ] Configuração mais fácil
- [ ] sex


## 📦 Requisitos
- Python **3.9+**
- Java (17+) instalado e configurado no `PATH`
- Servidor de Minecraft configurado (se ja tiver um, mova-o pra pasta "servidor")
- RCON ativado no `server.properties`

## 🚀 Instalação
Clone o repositório:
```
git clone https://github.com/DarkOFC73/painel-minecraft-flask.git
cd painel-minecraft-flask
```
Crie e ative um ambiente virtual:

``python -m venv venv``

``venv\Scripts\activate`` se usar windows

``source venv/bin/activate`` se for oprimido (Linux/Mac)

Instale as dependências:

``pip install -r requirements.txt``

## ⚙️ Configuração

Crie um arquivo .env na raiz do projeto:
```
PASSWORD=sua_senha_aqui
SECRET_KEY=uma_chave_secreta
JAR_NAME=server.jar
RCON_PASSWORD=sua_senha_rcon
RCON_PORT=25575
```


Certifique-se de que o server.properties do Minecraft contém:
```
enable-rcon=true
rcon.password=sua_senha_rcon
rcon.port=25575
```
## ▶️ Executando
no terminal:

``python app.py``

O painel estará disponível em:

http://127.0.0.1:5000


## 📝 Licença

Este projeto é licenciado sob a MIT License.

![Feito%20com-Python-3776AB?logo=python&logoColor=white](https://img.shields.io/badge/Feito%20com-Python-3776AB?logo=python&logoColor=white)
