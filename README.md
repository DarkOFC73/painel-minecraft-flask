# 🌸 Painel Minecraft em Flask

Um painel web simples, fofinho 💖 e ligeiramente milagroso ✨ para gerenciar seu servidor de Minecraft diretamente do navegador.  
Feito com Python + Flask, gambiarra e café.

[🇺🇸 Versão em inglês aqui!](README-en.md)

> "Isso **provavelmente** não deveria funcionar, mas funciona. E melhor do que deveria."  
> — Alguém que claramente não testou o suficiente

![GitHub last commit](https://img.shields.io/github/last-commit/DarkOFC73/painel-minecraft-flask)
![Issues abertas](https://img.shields.io/github/issues/DarkOFC73/painel-minecraft-flask)
![Stars](https://img.shields.io/github/stars/DarkOFC73/painel-minecraft-flask?style=social)



---

## ✨ Funcionalidades

- 🟢 **Iniciar / Parar o servidor**  
  Porque apertar um botão é mais legal do que digitar no terminal.
- 🎮 **Contador de jogadores online** (via RCON)  
  Veja quantos amigos ignoraram seu convite pra jogar.
- 📁 **Gerenciador de arquivos** (editar, baixar, enviar arquivos)  
  *A verdadeira experiência FTP... sem o trauma.*
- 💾 **Backup completo do mundo**, incluindo todas as dimensões  
  Porque ninguém quer perder aquele castelo de terra no Nether.
- 🔍 **Visualização de logs em tempo real**  
  Espione seu servidor como um verdadeiro FBI da Mojang.
- ⚙️ **Edição do arquivo `.env`** diretamente pelo painel  
  Menos tempo no terminal, mais tempo quebrando blocos.
- 📊 **Monitoramento de uso de RAM e CPU**  
  Ideal pra quando seu servidor for possuído por um mod bugado.
- ⌨️ **Comandos rápidos RCON**  
  Porque digitar `/stop` nunca foi tão prazeroso.
- 🎨 **Interface totalmente reformulada**  
  Mais bonita que a UI do Minecraft 1.20 (sem shade).
- 🌐 ~~Integração com playit.gg para acesso remoto~~ *(em desenvolvimento. talvez. um dia. quem sabe.)*
- ✅ **Compatível com:** Forge, Fabric, Vanilla e Paper  
  ❌ *BungeeCord e Velocity ainda estão de castigo.*

---

## 🔮 Funcionalidades futuras

- [ ] Deletar arquivos direto do painel (sem acidentes, prometo!)
- [ ] Integração funcional com Playit.gg (alô devs, me ajuda aí)
- [x] Backups automáticos, porque esquecer é humano
- [x] Tela de configurações mais intuitiva e menos deprimente
- [ ] Modo noturno (porque os olhos choram)
- [ ] ~~sex~~ (💀 ainda não é esse tipo de painel)

---

## 📦 Requisitos

- Python **3.9 ou superior**
- Java (versão 17+) instalado e no `PATH`
- Um servidor Minecraft (coloque na pasta `servidor`)
- RCON ativado no `server.properties`

> Dica: use um server `.jar` leve pra testar, tipo Paper ou Vanilla sem mods pesadões

---

## 🚀 Instalação

Clone o repositório:
```
git clone https://github.com/DarkOFC73/painel-minecraft-flask.git
cd painel-minecraft-flask
```
Crie e ative um ambiente virtual:
```
python -m venv venv

    #Windows (servidor no windows? serio?):
    venv\Scripts\activate

    #Linux/macOS:
    source venv/bin/activate
```
Instale as dependências:
```
pip install -r requirements.txt
```
⚙️ Configuração

Crie um arquivo .env com esse conteúdo maroto:
```
SECRET_KEY=chave_secreta_gerenositeplsplspls
PASSWORD=admin
SERVER_DIR=caminho/pro/servidor
JAR_NAME=paper.jar
PLAYIT_PATH=./playit
RCON_PASSWORD=nyan
RCON_PORT=25575
# Configurações do Playit.gg (opcionais)
PLAYIT_API_KEY=sua_api_key_aqui
PLAYIT_TUNNEL_ID=seu_tunnel_id_aqui
PLAYIT_AGENT_PATH=./playit-agent
# Configurações de Backup Automático
AUTO_BACKUP_ENABLED=false
AUTO_BACKUP_INTERVAL=3600
AUTO_BACKUP_KEEP=5
```
Agora edite o server.properties do Minecraft:
```
enable-rcon=true
rcon.password=sua_senha_rcon
rcon.port=25575
```
   Se você não ativar o RCON, nada vai funcionar. Nada. Zero. Nem o botão de parar o servidor. Nem seu coraçãozinho 💔

▶️ Executando

Abra o terminal e mande o brabo:
```
python app.py
```
Abra o navegador e vá para:

    http://127.0.0.1:5000

Se tudo deu certo, parabéns. Se não deu, parabéns também: você é oficialmente um dev de Flask agora. 😎
# 📝 Licença

Este projeto é licenciado sob a MIT License.
Pode usar, quebrar, arrumar e chamar de seu. Só não culpe o autor se der ruim.

Feito com Python
