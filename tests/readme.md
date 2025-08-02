# 🌸 Painel Minecraft em Flask

Um painel web simples e fofinho 💖 para gerenciar um servidor de Minecraft diretamente do navegador, feito com Python + Flask.

> isso **provavelmente** não deveria funcionar, mas funciona. - O criador desse projeto

## ✨ Funcionalidades
- 🟢 **Iniciar / Parar servidor**
- 🎮 **Contador de jogadores online** (via RCON)
- 📁 **Gerenciador de arquivos** (editar, baixar, enviar arquivos)
- 💾 **Opção para backup** do mundo
- 🔍 **Visualização de logs** em "tempo real"
- 🌐 **Integração com Playit.gg** para acesso remoto

## 🔜 Coisas a serem adicionadas
- [x] Opção pra deletar arquivos (pretendo adicionar pra sair com o release do playit)
- [x] Integração com Playit.gg
- [x] Backup automático
- [ ] Configuração mais fácil (não sei como fazer isso :/)

## 📦 Requisitos
- Python **3.9+**
- Java (17+) instalado e configurado no `PATH`
- Servidor de Minecraft configurado (se ja tiver um, mova-o pra pasta "servidor")
- RCON ativado no `server.properties`
- **(Opcional) Agente do Playit.gg** para acesso remoto

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
# Configurações do Playit.gg (opcional)
PLAYIT_API_KEY=sua_api_key_aqui
PLAYIT_TUNNEL_ID=seu_tunnel_id_aqui
PLAYIT_AGENT_PATH=./playit-agent
```

## 🌐 Configuração do Playit.gg (Opcional mas Recomendado)

O Playit.gg permite acesso remoto ao seu servidor Minecraft. Esta integração é totalmente opcional.

### 1. Instalação do Agente do Playit

```bash
# Criar pasta para o Playit
mkdir playit
cd playit

# Linux
wget https://github.com/playit-cloud/playit-agent/releases/latest/download/playit-linux
chmod +x playit-linux

# Windows: Baixe playit-windows.exe do site oficial
# Mac: Baixe playit-mac do site oficial
```

### 2. Configuração no Painel do Playit.gg

1. Acesse [https://playit.gg](https://playit.gg) e crie uma conta
2. Faça login no painel
3. Vá em "Tunnels" e crie um novo túnel:
   - **Type**: Minecraft Java
   - **Local Port**: 25565 (porta do seu servidor)
   - **Name**: Escolha um nome (ex: "Meu Servidor Minecraft")
4. Anote o **Tunnel ID** mostrado nos detalhes do túnel

### 3. Configuração da API Key

1. No painel do Playit.gg, vá em **Settings** > **API Keys**
2. Clique em **Create API Key**
3. Dê um nome à key e clique em **Create**
4. Copie o token gerado

### 4. Configuração no .env

Adicione estas linhas ao seu arquivo `.env`:

```
# Configurações do Playit.gg (opcional)
PLAYIT_API_KEY=sua_api_key_aqui
PLAYIT_TUNNEL_ID=seu_tunnel_id_aqui
PLAYIT_AGENT_PATH=./playit/playit-linux
```

### 5. Uso no Painel

- O painel mostrará o status do agente Playit (Online/Offline)
- Use os botões "Iniciar Playit.gg" e "Parar Playit.gg" para controlar o agente
- Se configurado, as informações do túnel aparecerão na página principal
- O link de acesso remoto será mostrado quando disponível

**Observação**: O Playit.gg é opcional. O painel funciona normalmente sem esta configuração.

## ▶️ Executando
no terminal:

``python app.py``

O painel estará disponível em:

http://127.0.0.1:5000

## 📝 Licença

Este projeto é licenciado sob a MIT License.

![Feito%20com-Python-3776AB?logo=python&logoColor=white](https://img.shields.io/badge/Feito%20com-Python-3776AB?logo=python&logoColor=white)


> "After 9 Years of development, hopefully it would have been worth the wait. Thanks and have fun." - Gabe Newell
