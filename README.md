# 💙 Lumine D'Lumière — Discord Bot

> *"Estou pronta pra te servir! Posso te ajudar com várias coisinhas~"*

Lumine é uma bot de Discord com personalidade de maid fofa, feita para ser companheira de servidor. Ela toca música via Lavalink, gerencia playlists pessoais, tem um sistema completo de café/barista com progressão de XP, busca informações de Pokémon e rola dados de RPG — tudo com mensagens carinhosas e personalidade própria.

---

## ✨ Funcionalidades

### 🎵 Música

Powered by **Lavalink** + **Wavelink**. Suporta YouTube, YouTube Music, SoundCloud, Bandcamp, Twitch, Vimeo e HTTP direto.

| Comando | Descrição |
|---|---|
| `l!play <nome/link>` | Toca ou adiciona à fila 🎶 |
| `l!play @playlist` | Toca sua playlist pessoal 💙 |
| `l!play @playlist @Usuario` | Toca a playlist de outra pessoa 🌟 |
| `l!skip` / `l!sk` | Pula a música atual ⏭️ |
| `l!jump <N>` | Pula N músicas da fila de uma vez |
| `l!pause` | Pausa a música ⏸️ |
| `l!resume` | Retoma a música pausada ▶️ |
| `l!stop` / `l!leave` | Para tudo e sai do canal ⏹️ |
| `l!queue` / `l!q` | Fila paginada com botões ⬅️ ➡️ |
| `l!nowplaying` / `l!np` | Música atual com barra de progresso ⏳ |
| `l!remove $N` | Remove a música de posição #N da fila 🗑️ |
| `l!remove <N>` | Remove as próximas N músicas |
| `l!clear` | Limpa a fila inteira 🧹 |
| `l!shuffle` | Embaralha a fila aleatoriamente 🔀 |
| `l!loop` / `l!lp` | Loop da música atual 🔁 |
| `l!seek <tempo>` | Pula para um tempo — ex: `l!seek 1:30` ⏩ |
| `l!volume [0-150]` | Mostra ou altera o volume 🔊 |

**Comportamentos automáticos:**
- **Auto-leave:** se o canal de voz ficar vazio, a Lumine aguarda **2 minutos** e sai com uma mensagem fofa.
- **Pause watcher:** quando pausada, a Lumine pinga quem pausou a cada **10 minutos** com lembretes carinhosos — ela nunca sai por causa de pausa, só fica esperando.
- **Track start embed:** ao iniciar uma nova música, envia automaticamente um embed com título, autor, duração e thumbnail.
- **Spotify:** reconhece links do Spotify mas está temporariamente desativado (a API exige conta Premium no app).

---

### 🎵 Playlists Pessoais

Sistema de playlists salvas por usuário, persistidas em `data/playlists.json`.

| Comando | Descrição |
|---|---|
| `l!playlist save <nome>` | Salva a fila atual (+ música tocando) como playlist 💾 |
| `l!playlist list` | Suas playlists 📋 |
| `l!playlist list @Usuario` | Playlists de outra pessoa |
| `l!playlist show <nome>` | Espia as músicas (paginação com botões) 👀 |
| `l!playlist show <nome> @Usuario` | Ver playlist de outra pessoa |
| `l!playlist add <nome>` | Adiciona a música atual à playlist |
| `l!playlist add <nome> <N>` | Adiciona a música #N da fila |
| `l!playlist add <nome> <url>` | Adiciona por link direto 🔗 |
| `l!playlist remove <nome> <N>` | Remove a música #N da playlist 🗑️ |
| `l!playlist delete <nome>` | Apaga a playlist inteira 💔 |
| `l!playlist rename <nome> <novo>` | Renomeia com carinho ✏️ |
| `l!playlist loop` | Ativa/desativa loop da fila inteira 🔁 |

**Aliases:** `l!pl` para todos os subcomandos acima.

**Limites:** até **5 playlists** por usuário, **200 músicas** por playlist.

---

### ☕ Café da Lumine

Sistema completo de simulação de cafeteria com economia, XP, progressão de barista, receitas secretas e clientes NPC — persistido em `data/cafe_data.json`.

#### Economia e Trabalho

| Comando | Descrição |
|---|---|
| `l!trabalhar` | Ganha 30–90 Lumicoins (cooldown: **30 min**) 💼 |
| `l!cafe` | Seu perfil de barista: moedas, XP, nível, estoque, upgrades ⭐ |
| `l!ranking cafe` | Top 10 baristas do servidor 🏆 |

#### Loja e Compras

| Comando | Descrição |
|---|---|
| `l!loja` | Ingredientes disponíveis com preços 🏪 |
| `l!comprar <item> [qtd] ...` | Compra vários ingredientes de uma vez 🛍️ |

**21 ingredientes** em 5 categorias: Básicos e Grãos, Laticínios, Adoçantes e Xaropes, Especiarias e Ervas, Frutas e Extras.

**Promoção diária:** uma categoria diferente recebe **30% de desconto** a cada dia (determinístico — mesma promoção para todos).

#### Preparo e Venda

| Comando | Descrição |
|---|---|
| `l!cardapio` | Receitas públicas e preços de venda 📋 |
| `l!preparar <bebida> [qtd]` | Prepara até 20 unidades de uma vez ☕ |
| `l!vender <bebida>` | Vende 1 unidade do estoque 💰 |

**8 bebidas públicas** (Café Simples, Cappuccino, Latte, Café Gelado, Frappuccino, Caramel Macchiato, Matcha Latte, Mocha) e **15 receitas secretas** aguardando descoberta.

**Bebida do dia:** uma bebida ganha **+50% XP** ao preparar e **+30% no preço** de venda (determinístico por dia).

#### Receitas Secretas

| Comando | Descrição |
|---|---|
| `l!inventar <ing1> <ing2> ...` | Combina ingredientes e descobre receitas ocultas 🧪 |

Ao descobrir uma receita pela primeira vez: **XP dobrado** + **100 Lumicoins de bônus**. Ingredientes são consumidos mesmo em tentativas erradas.

**15 receitas secretas:** Café das Arábias, Mocha Branco de Inverno, Cold Brew de Limão, Café com Sal Marinho, Frapê de Morango Selvagem, Latte de Flor de Cerejeira, Choconta, Gingerbread Latte, Cocoa Espresso, Lágrimas de Anjo, Honey Citrus Tea, Bomba de Gelo, Café Cubano, Pink Matcha, Beijo de Caramelo Salgado.

**Sistema de pistas:** durante atendimentos e no `l!cardapio`, a Lumine e os clientes NPC dão pistas narrativas sutis sobre receitas ainda não descobertas.

#### Atendimento de Clientes

| Comando | Descrição |
|---|---|
| `l!atender` | Recebe um novo cliente (cooldown: **60 min**) 👥 |
| `l!atender <bebida>` | Serve o cliente pendente ou "rouba" o de outro barista |

**6 clientes NPC** com personalidades únicas: Mia (tímida 🐱), Rex (animado 🐶), Lúcia (elegante 🦊), Pip (curioso 🐹), Stella (sonhadora 🐰) e Bruno (faminto 🐻). Cada um tem falas diferentes para pedido, agradecimento, recusa e atendimento roubado.

**Mecânica de roubo:** se você tiver uma bebida preparada que coincide com o pedido pendente de outro barista no servidor, pode atender o cliente dele antes que ele o faça.

Cada atendimento bem-sucedido rende **20–60 moedas** + **5–15 XP** (com bônus da cafeteira).

#### Cafeteira (Upgrades)

| Comando | Descrição |
|---|---|
| `l!cafeteira` | Vê os upgrades disponíveis e o nível atual ☕ |
| `l!melhorar cafeteira` | Compra a próxima melhoria ✨ |

**6 níveis de cafeteira** (0–5), cada um aumentando bônus de venda, XP e atendimento:

| Nível | Nome | Custo | Bônus Venda | Bônus XP | Bônus Atend. |
|---|---|---|---|---|---|
| 0 | Cafeteira Inicial | — | 0% | 0% | 0% |
| 1 | Cafeteira Polida | 300 💰 | +5% | +5% | 0% |
| 2 | Caldeira Reforçada | 750 💰 | +10% | +10% | 0% |
| 3 | Moedor Embutido | 1.500 💰 | +15% | +15% | +5% |
| 4 | Máquina Profissional | 3.000 💰 | +20% | +20% | +10% |
| 5 | Luminepressa Deluxe | 6.000 💰 | +30% | +25% | +15% |

#### Progressão de Barista (XP e Níveis)

| Nível | Título | XP necessário |
|---|---|---|
| 1 | Barista Novato ☕ | 0 |
| 2 | Barista Aprendiz ☕ | 100 |
| 3 | Barista Experiente ☕ | 300 |
| 4 | Barista Sênior 🌟 | 700 |
| 5 | Mestre Barista 🌟 | 1.500 |
| 6 | Lenda do Café 👑 | 3.000 |

---

### 🎮 Pokémon

Consulta a **PokéAPI** (gratuita, sem autenticação). Suporta os 1025 Pokémon das Gerações I–IX.

| Comando | Descrição |
|---|---|
| `l!pokemon` | Curiosidade sobre um Pokémon **aleatório** 🎲 |
| `l!pokemon <nome>` | Busca por nome — ex: `l!pokemon charizard` |
| `l!pokemon <número>` | Busca por número — ex: `l!pokemon 006` |

O embed exibe: tipo (com emoji e cor temática), geração, peso e altura, habilidades normais e oculta, texto da Pokédex (sorteado aleatoriamente entre os jogos, com prioridade para pt-BR), stats base com barra visual (HP, ATK, DEF, SpA, SpD, SPD + total), artwork oficial como thumbnail e badge de Lendário/Mítico.

**Aliases:** `l!pokedex`, `l!poke`

---

### 🎲 Dados

| Comando | Descrição |
|---|---|
| `l!roll <expressão>` | Rola dados 🎲 |

**Formatos aceitos:**
- `NdX` — N dados de X faces. Ex: `3d6`
- `NdX+M` ou `NdX-M` — com modificador. Ex: `1d20+5`
- `T#NdX+M` — repete T vezes. Ex: `5#3d6+2`

**Limites:** até 100 repetições, 100 dados, 10.000 faces.

**Aliases:** `l!r`, `l!rolar`

> **✨ Atalho mágico:** mande **só** a expressão no chat (ex: `2d6`) e a Lumine rola automaticamente — sem precisar do prefixo! Funciona apenas quando a mensagem é somente a expressão.

---

### 💙 Help

| Comando | Descrição |
|---|---|
| `l!help` | Cardápio geral com todas as categorias |
| `l!help <categoria>` | Página detalhada de uma categoria |

Categorias disponíveis: `musica`, `dados`, `pokemon`, `cafe`.
Sistema extensível: qualquer cog que implemente `help_meta()` e `help_field()` aparece automaticamente. Cogs podem injetar seções extras em outras categorias via `help_field_extra()`.

**Aliases:** `l!ajuda`, `l!comandos`

---

## 🗂️ Estrutura do Projeto

```
Discord_LumineDLumiere/
├── core.py                  # Inicialização do bot, Lavalink local e carregamento de cogs
├── requirements.txt         # Dependências Python
├── .env                     # Tokens e segredos (não sobe pro Git!)
├── .gitignore
│
├── cogs/                    # Módulos de funcionalidade (cada um é um Cog)
│   ├── __init__.py
│   ├── help.py              # Sistema de ajuda dinâmico (l!help)
│   ├── music.py             # Música via Lavalink/Wavelink (l!play, l!queue, etc.)
│   ├── playlists.py         # Playlists pessoais (l!pl save/list/show/add/...)
│   ├── dice.py              # Rolagem de dados RPG (l!roll + auto-detect)
│   ├── pokemon.py           # Consulta PokéAPI (l!pokemon)
│   └── cafe/                # Sistema de cafeteria (módulo dividido em camadas)
│       ├── __init__.py
│       ├── cog.py           # Comandos Discord do café (camada de apresentação)
│       ├── service.py       # Lógica de negócio pura (sem Discord)
│       ├── repository.py    # Persistência e acesso aos dados (JSON via JsonStore)
│       ├── catalog.py       # Catálogo: ingredientes, bebidas, receitas, upgrades, níveis
│       ├── narrative.py     # Textos: clientes NPC, pistas, frases da Lumine
│       ├── images.py        # Busca de imagens de anime (nekos.best / waifu.pics)
│       └── daily.py         # Promoção diária e bebida do dia (determinístico por data)
│
├── utils/                   # Infraestrutura compartilhada
│   ├── __init__.py
│   ├── paths.py             # Caminhos absolutos para os arquivos de dados
│   └── storage.py           # JsonStore: leitura/escrita atômica com lock assíncrono
│
├── data/                    # Dados persistidos localmente (ignorados pelo Git)
│   ├── cafe_data.json        # Dados dos baristas (moedas, XP, ingredientes, etc.)
│   ├── cafe_data.example.json
│   ├── playlists.json        # Playlists salvas pelos usuários
│   └── playlists.example.json
│
└── bin/                     # Lavalink e Java portátil
    ├── Lavalink.jar          # Baixe manualmente (não está no repositório)
    ├── application.yml       # Configuração do servidor Lavalink (não sobe pro Git!)
    ├── application.yml.example
    ├── jre/                  # Java 17 portátil (não está no repositório)
    └── plugins/              # Plugins do Lavalink baixados automaticamente
```

---

## ⚙️ Arquitetura Interna

### Lavalink automático
O `core.py` verifica se a porta `2333` já está em uso. Se não estiver, inicia o `Lavalink.jar` usando o Java portátil em `bin/jre/`. Ao encerrar o bot, o processo do Lavalink é terminado automaticamente.

### JsonStore (`utils/storage.py`)
Abstração de persistência JSON com:
- **Lock assíncrono por arquivo** — sem corridas entre comandos simultâneos.
- **Escrita atômica** — salva em `.tmp` e substitui o arquivo original via `os.replace`.
- Métodos: `read()`, `replace()`, `update(mutator)`.

### Sistema de Help extensível (`cogs/help.py`)
Cada cog expõe:
- `help_meta()` → chave de busca, aliases, ícone, categoria, descrição curta.
- `help_field()` → título e corpo do campo detalhado.
- `help_field_extra()` *(opcional)* → injeta uma seção extra em outra categoria (usado por `playlists.py` para adicionar a seção de playlists dentro de `l!help musica`).

### Café — separação em camadas
| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Apresentação | `cog.py` | Recebe comandos Discord, formata embeds, chama repository |
| Negócio | `service.py` | Lógica pura (sem Discord): trabalhar, comprar, preparar, inventar, vender, atender |
| Dados | `repository.py` | Lê/escreve `cafe_data.json` via `JsonStore`; coordena o atendimento com roubo |
| Catálogo | `catalog.py` | Constantes: ingredientes, bebidas, receitas, upgrades, cooldowns, níveis |
| Narrativa | `narrative.py` | Textos de clientes, pistas de receitas, frases da Lumine |
| Imagens | `images.py` | Cache de imagens de anime com TTL (nekos.best → waifu.pics como fallback) |
| Diário | `daily.py` | Promoção e bebida do dia, determinísticas por semente da data |

---

## 🚀 Como Rodar

### Pré-requisitos

- Python 3.11+
- Java 17 (portátil em `bin/jre/` **ou** instalado no sistema)
- `Lavalink.jar` em `bin/` (baixe em [github.com/lavalink-devs/Lavalink/releases](https://github.com/lavalink-devs/Lavalink/releases))

### Instalação

```bash
# 1. Clone o repositório
git clone https://github.com/seu-usuario/Discord_LumineDLumiere.git
cd Discord_LumineDLumiere

# 2. Crie e ative o ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Configure os segredos
cp bin/application.yml.example bin/application.yml
# Edite o arquivo e preencha os tokens
```

### Configuração (`.env`)

Crie um arquivo `.env` na raiz com:

```env
DISCORD_TOKEN=seu_token_aqui
LAVALINK_PASSWORD=sua_senha_do_lavalink
YOUTUBE_REFRESH_TOKEN=token_oauth_youtube   # necessário para YouTube
SPOTIFY_CLIENT_ID=opcional
SPOTIFY_CLIENT_SECRET=opcional
```

### Execução

```bash
python core.py
```

O bot inicializa o Lavalink automaticamente (se `bin/Lavalink.jar` e `bin/jre/` existirem) e carrega todos os cogs. O Lavalink é encerrado automaticamente junto com o bot.

---

## 📦 Dependências

```
discord.py[voice]    # biblioteca principal do Discord
python-dotenv        # carregamento do .env
wavelink             # wrapper para o servidor Lavalink
```

---

## 🔒 Segurança e Git

Os seguintes arquivos **nunca sobem** para o repositório (`.gitignore`):

| Arquivo / Pasta | Motivo |
|---|---|
| `.env` | Token do bot e segredos |
| `bin/application.yml` | Tokens OAuth do YouTube e chaves do Spotify |
| `bin/Lavalink.jar` | Binário pesado (~96 MB) |
| `bin/jre/` | Java portátil (~200 MB) |
| `bin/plugins/` | Plugins do Lavalink baixados automaticamente |
| `data/*.json` | Dados de usuários (privacidade) |
| `venv/` | Ambiente virtual Python |

Use os arquivos `.example` como base para configuração local.

---

## 🎀 Persona da Lumine

A Lumine D'Lumière é uma maid virtual com personalidade carinhosa e fofa. Características:
- Usa expressões como "~", "💙", "✨", "🥺" nas mensagens.
- Tem frases únicas para cada situação (trabalhar, inventar, atender clientes, avisos de pausa).
- Clientes NPC têm personalidades distintas com falas únicas.
- O sistema de pistas de receitas é narrado de forma poética e indireta.

---

*Feito com 💙 e muito café.*
