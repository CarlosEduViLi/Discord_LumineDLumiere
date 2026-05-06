<div align="center">

<img src="https://media.giphy.com/media/l0Iy33dWjmywkCnNS/giphy.gif" width="280" alt="Lumine D'Lumière acenando~"/>

# ✨ Lumine D'Lumière💙
### *Sua bot musical fofa e amorosa do Discord~*

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![discord.py](https://img.shields.io/badge/discord.py-2.x-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://github.com/Rapptz/discord.py)
[![Wavelink](https://img.shields.io/badge/Wavelink-3.x-1DB954?style=for-the-badge&logo=soundcloud&logoColor=white)](https://wavelink.dev)
[![Lavalink](https://img.shields.io/badge/Lavalink-4.x-orange?style=for-the-badge)](https://github.com/lavalink-devs/Lavalink)

> *"Deixa que eu cuido da trilha sonora do seu dia~ 🎵💙"*

</div>

---

## 💙 Quem é a Lumine?

A **Lumine** é uma bot do Discord feita com muito carinho, pensada para ser a companheira musical perfeita do seu servidor. Ela não é só uma bot qualquer — ela tem **personalidade**, é **fofa**, **aconchegante** e acima de tudo, **amorosa** com todos que pedem uma musiquinha pra ela~ 🌸

Construída sobre **Lavalink + Wavelink**, a Lumine entrega áudio de alta qualidade, gerenciamento completo de filas, playlists pessoais e muito mais — tudo com mensagens cheias de carinho!

---

## 🌟 O que a Lumine pode fazer?

### 🎵 Música
- Tocar músicas do **YouTube** e **YouTube Music** por nome ou link
- Gerenciar uma **fila completa** com paginação por botões ⬅️ ➡️
- Mostrar **progresso em tempo real** da música com barra visual: `` `1:22` ━━━━●──── `3:00` ``
- **Pular**, **embaralhar**, **remover** e **mover** músicas da fila
- Controle de **volume** (0–150%)
- **Loop** da música atual 🔁 e **loop da fila inteira** 🔁
- **Seek** — ir para qualquer ponto da música: `l!seek 1:30`

### 📋 Playlists Pessoais
- **Salvar** a fila atual como playlist com nome personalizado
- **Até 5 playlists** por usuário, com **até 200 músicas** cada
- **Tocar** qualquer playlist sua: `l!play @lofi`
- **Tocar** a playlist de outra pessoa: `l!play @lofi @Amigo`
- **Adicionar** músicas por link, posição na fila, ou a que está tocando
- **Loop de playlist** inteira ao carregar
- Carregamento com **barra de progresso animada** fofa 🎀

### 💬 Personalidade
- Mensagens fofas e amorosas em **todos os momentos**
- **Auto-saída** do canal de voz após 2 minutos sem ninguém
- **Lembretes carinhosos** ao ficar pausada por muito tempo
- Frases exclusivas da Lumine para cada situação~ 🌸

### 🎲 Extras
- **Sistema de café** — trabalhe, compre ingredientes, prepare bebidas e atenda clientes!
- **Dados** — role dados de qualquer tipo: `l!roll 2d6+3`
- **Curiosidades Pokémon** — descubra fatos sobre qualquer Pokémon via PokéAPI~ 🎮

---

## ⚙️ Configuração

### Pré-requisitos

- **Python 3.10+**
- **Java 17+** (para o Lavalink)
- Uma conta no [Discord Developer Portal](https://discord.com/developers/applications)

### 1. Clone o repositório

```bash
git clone https://github.com/SEU_USUARIO/Discord_LumineDLumiere.git
cd Discord_LumineDLumiere
```

### 2. Crie o ambiente virtual e instale as dependências

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

pip install -r requirements.txt
```

### 3. Configure o `.env`

Crie um arquivo `.env` na raiz do projeto:

```env
DISCORD_TOKEN=seu_token_aqui
```

> 🔒 **Nunca suba seu token pro GitHub!** O `.env` já está no `.gitignore`.

### 4. Configure o Lavalink

Baixe o `Lavalink.jar` em [lavalink-devs/Lavalink/releases](https://github.com/lavalink-devs/Lavalink/releases) e coloque dentro da pasta `bin/`.

A Lumine também precisa de uma **JRE portátil** na pasta `bin/jre/`. Você pode baixar do [Adoptium](https://adoptium.net/) e extrair lá.

A configuração do servidor está em `bin/application.yml` — já vem pronta!

### 5. Inicie a Lumine!

```bash
python core.py
```

A Lumine vai subir o Lavalink automaticamente e se conectar ao Discord~ 💙

---

## 📖 Comandos

> **Prefixo:** `l!`

### 🎵 Música

| Comando | Descrição |
|---|---|
| `l!play <nome ou link>` | Toca ou adiciona à fila 🎶 |
| `l!play @playlist` | Toca sua playlist salva 💙 |
| `l!play @playlist @Usuario` | Toca a playlist de outra pessoa 🌟 |
| `l!skip` / `l!sk` | Pula a música atual ⏭️ |
| `l!jump <N>` | Pula N músicas de uma vez |
| `l!pause` / `l!resume` | Pausa ⏸️ e retoma ▶️ |
| `l!stop` | Para tudo e saio do canal ⏹️ |
| `l!queue` / `l!q` | Mostra a fila com botões de página |
| `l!nowplaying` / `l!np` | Música atual com barra de progresso ⏳ |
| `l!loop` / `l!lp` | Loop da música atual 🔁 |
| `l!seek <tempo>` | Vai para um tempo específico (ex: `1:30`) ⏩ |
| `l!volume <0-150>` | Ajusta o volume 🔊 |
| `l!shuffle` | Embaralha a fila 🔀 |
| `l!clear` | Limpa toda a fila 🧹 |
| `l!remove $N` / `l!rm N` | Remove música(s) da fila 🗑️ |

### 📋 Playlists

| Comando | Descrição |
|---|---|
| `l!pl save <nome>` | Salva a fila atual como playlist 💾 |
| `l!pl list` | Suas playlists 📋 |
| `l!pl show <nome>` | Espia as músicas da playlist 👀 |
| `l!pl add <nome>` | Adiciona a música atual à playlist |
| `l!pl add <nome> <url>` | Adiciona por link direto 🔗 |
| `l!pl remove <nome> <N>` | Remove uma música da playlist 🗑️ |
| `l!pl delete <nome>` | Apaga a playlist inteira 💔 |
| `l!pl rename <nome> <novo>` | Renomeia com carinho ✏️ |
| `l!pl loop` | Loop da fila inteira 🔁 |

### 🎮 Pokémon

| Comando | Descrição |
|---|---|
| `l!pokemon` | Curiosidade sobre um Pokémon **aleatório** 🎲 |
| `l!pokemon <nome>` | Busca por nome — ex: `l!pokemon charizard` |
| `l!pokemon <número>` | Busca por número — ex: `l!pokemon 006` |

> Exibe tipo, geração, habilidades, texto da Pokédex (sorteado aleatoriamente entre os jogos), stats com barra visual e badge de Lendário/Mítico. Aliases: `l!pokedex`, `l!poke`.

### ☕ Café da Lumine

| Comando | Descrição |
|---|---|
| `l!trabalhar` | Ganhe Lumicoins (cooldown 30 min) 💼 |
| `l!loja` | Ingredientes à venda 🏪 |
| `l!comprar <item> [qtd]` | Compre ingredientes 🛍️ |
| `l!cardapio` | Veja receitas e preços 📋 |
| `l!preparar <bebida>` | Prepare uma bebida ☕ |
| `l!vender <bebida>` | Venda do estoque 💰 |
| `l!atender [bebida]` | Atenda um cliente especial 👥 |
| `l!cafe` | Seu perfil de barista ⭐ |
| `l!ranking cafe` | Top 10 baristas 🏆 |

### 🎲 Dados

| Comando | Descrição |
|---|---|
| `l!roll <expressão>` | Ex: `l!roll 1d20+5`, `l!roll 5#3d6` 🎲 |

> **Atalho mágico:** mande só a expressão no chat (ex: `2d6`) e a Lumine rola automaticamente!

---

## 🗂️ Estrutura do Projeto

```
Discord_LumineDLumiere/
├── core.py              # Inicialização do bot e Lavalink
├── requirements.txt     # Dependências Python
├── .env                 # Token (não sobe pro Git!)
├── .gitignore
├── bin/
│   ├── application.yml  # Configuração do servidor Lavalink
│   ├── Lavalink.jar     # Baixe manualmente (não está no repo)
│   └── jre/             # Java portátil (não está no repo)
└── cogs/
    ├── music.py         # Comandos de música 🎵
    ├── playlists.py     # Sistema de playlists 📋
    ├── playlists.json   # Dados salvos das playlists
    ├── cafe.py          # Sistema de café ☕
    ├── cafe_core.py     # Lógica e dados do café
    ├── cafe_data.json   # Dados persistidos dos usuários
    ├── dice.py          # Dados 🎲
    ├── pokemon.py       # Curiosidades Pokémon via PokéAPI 🎮
    └── help.py          # Sistema de ajuda 💙
```

---

## 🛠️ Tecnologias

| Tecnologia | Função |
|---|---|
| [discord.py 2.x](https://github.com/Rapptz/discord.py) | Framework do bot |
| [Wavelink 3.x](https://wavelink.dev) | Wrapper para o Lavalink |
| [Lavalink 4.x](https://github.com/lavalink-devs/Lavalink) | Servidor de áudio de alta performance |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | Leitura do `.env` |
| [aiohttp](https://docs.aiohttp.org) | Requisições HTTP assíncronas (PokéAPI) |
| [PokéAPI](https://pokeapi.co) | Dados de Pokémon — gratuita, sem autenticação |

---

<div align="center">

<img src="https://media.giphy.com/media/rYKorlR2RtWnTlHfhI/giphy.gif" width="200" alt="Lumine D'Lumière fofa~"/>

*Feito com muito amor e carinho~ 💙✨*

*Se a Lumine te alegrou hoje, considera dar uma ⭐ no repositório!*

</div>
