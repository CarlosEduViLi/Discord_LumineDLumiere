# 💙 Lumine D'Lumière — Discord Bot

> *"Estou pronta pra te servir! Posso te ajudar com várias coisinhas~"*

Lumine é uma bot Discord com personalidade de **maid fofa**, feita para ser companheira de servidor. Ela toca música via Lavalink, gerencia playlists pessoais, tem um sistema completo de café/barista com progressão de XP e conquistas, busca informações de Pokémon e rola dados de RPG — tudo com mensagens carinhosas, personalidade própria e um **humor que muda conforme o horário do dia**.

---

## ✨ Funcionalidades

### 🎵 Música

Powered by **Lavalink** + **Wavelink 3**. Suporta YouTube, YouTube Music, SoundCloud, Bandcamp, Twitch, Vimeo e HTTP direto.

| Comando | Aliases | Descrição |
|---|---|---|
| `l!play <nome/link>` | `p`, `tocar` | Toca ou adiciona à fila 🎶 |
| `l!play @playlist` | — | Toca sua playlist pessoal 💙 |
| `l!play @playlist @Usuario` | — | Toca a playlist de outra pessoa 🌟 |
| `l!skip` | `sk`, `pular` | Pula a música atual ⏭️ |
| `l!jump <N>` | `j` | Pula N músicas da fila de uma vez |
| `l!pause` | `pausar` | Pausa a música ⏸️ |
| `l!resume` | `retomar` | Retoma a música pausada ▶️ |
| `l!stop` | `parar`, `leave` | Para tudo e sai do canal ⏹️ |
| `l!queue [pág]` | `q`, `fila` | Fila paginada com botões ⬅️ ➡️ |
| `l!nowplaying` | `np`, `tocando` | Música atual com barra de progresso ⏳ |
| `l!remove $N` | `rm`, `del` | Remove a música de posição #N da fila 🗑️ |
| `l!remove <N>` | `rm`, `del` | Remove as próximas N músicas |
| `l!clear` | `limpar`, `c` | Limpa a fila inteira 🧹 |
| `l!shuffle` | `embaralhar`, `sh` | Embaralha a fila aleatoriamente 🔀 |
| `l!loop` | `lp` | Loop da música atual (toggle) 🔁 |
| `l!seek <tempo>` | `ir` | Vai para um tempo — ex: `l!seek 1:30` ⏩ |
| `l!volume [0-150]` | `vol` | Mostra ou altera o volume 🔊 |

**Comportamentos automáticos:**
- **Auto-leave:** se o canal de voz ficar vazio, a Lumine aguarda **2 minutos** e sai com uma mensagem fofa contextual (varia conforme o período do dia).
- **Pause watcher:** quando pausada, pinga quem pausou a cada **10 minutos** com lembretes carinhosos — ela nunca sai por causa de pausa, só fica esperando.
- **Track start embed:** ao iniciar uma nova música, envia automaticamente um embed com título, autor, duração e thumbnail.
- **Spotify:** reconhece links do Spotify mas está temporariamente desativado (a API exige conta Premium no app).

---

### 🎶 Playlists Pessoais

Sistema de playlists salvas por usuário, persistidas em `data/playlists.json`.

| Comando | Aliases | Descrição |
|---|---|---|
| `l!pl save <nome>` | `salvar` | Salva a fila atual (+ música tocando) como playlist 💾 |
| `l!pl list` | `listar` | Suas playlists 📋 |
| `l!pl list @Usuario` | — | Playlists de outra pessoa |
| `l!pl show <nome>` | `ver` | Espia as músicas (paginação com botões) 👀 |
| `l!pl show <nome> @Usuario` | — | Ver playlist de outra pessoa |
| `l!pl add <nome>` | `adicionar` | Adiciona a música atual à playlist |
| `l!pl add <nome> <N>` | — | Adiciona a música #N da fila |
| `l!pl add <nome> <url>` | — | Adiciona por link direto 🔗 |
| `l!pl remove <nome> <N>` | `remover` | Remove a música #N da playlist 🗑️ |
| `l!pl delete <nome>` | `deletar`, `apagar` | Apaga a playlist inteira 💔 |
| `l!pl rename <nome> <novo>` | `renomear` | Renomeia com carinho ✏️ |
| `l!pl loop` | `loopall` | Ativa/desativa loop da fila inteira 🔁 |

**Aliases:** `l!playlist` para todos os subcomandos acima.

**Limites:** até **5 playlists** por usuário, **200 músicas** por playlist. Nomes devem conter apenas letras, números, `-` ou `_` (máx. 20 caracteres).

---

### ☕ Café da Lumine

Sistema completo de simulação de cafeteria com economia, XP, progressão de barista, conquistas, receitas secretas, clientes NPC e interações entre jogadores — persistido em `data/cafe_data.json`.

#### Economia e Trabalho

| Comando | Aliases | Descrição |
|---|---|---|
| `l!trabalhar` | `work`, `trab`, `trabalha`, `labor` | Ganha 30–90 Lumicoins (cooldown: **30 min**) 💼 |
| `l!cafe` | `barista`, `perfil`, `profile`, `café` | Seu perfil de barista: moedas, XP, nível, estoque, ingredientes e cooldowns ⭐ |
| `l!ranking cafe` | `rank`, `top`, `leaderboard`, `placar` | Top 10 baristas do servidor por Lumicoins 🏆 |
| `l!dar @user <qtd>` | `give`, `pagar`, `send`, `transferir`, `enviar` | Transfere Lumicoins para outro barista 💸 |

#### Loja e Compras

| Comando | Aliases | Descrição |
|---|---|---|
| `l!loja [pág]` | `shop`, `store`, `mercado` | Ingredientes disponíveis com preços 🏪 |
| `l!comprar <item> [qtd] ...` | `buy`, `compra`, `purchase` | Compra vários ingredientes de uma só vez 🛍️ |

**21 ingredientes** em 5 categorias:

| Categoria | Ingredientes |
|---|---|
| ☕ Básicos e Grãos | Grão de Café, Gelo, Água |
| 🥛 Laticínios | Leite, Chantilly, Leite Condensado |
| 🍯 Adoçantes e Xaropes | Açúcar, Caramelo, Chocolate, Mel, Baunilha |
| 🌿 Especiarias e Ervas | Matcha, Canela, Menta, Pimenta, Sal Marinho, Gengibre |
| 🍓 Frutas e Extras | Limão, Morango, Coco, Flor de Cerejeira |

**Promoção diária:** uma categoria diferente recebe **desconto** a cada dia (determinístico — mesma promoção para todos no servidor).

#### Cafeteira (Upgrades)

| Comando | Aliases | Descrição |
|---|---|---|
| `l!cafeteira` | `upgrades`, `cafeteria`, `machine` | Vê o nível atual e os bônus ativos ☕ |
| `l!melhorar cafeteira` | `upgrade`, `melhora`, `improve` | Compra a próxima melhoria ✨ |

**6 níveis de cafeteira** (0–5), cada upgrade aumenta bônus de venda, XP ao preparar e gorjeta ao atender:

| Nível | Nome | Custo | Bônus Venda | Bônus XP | Bônus Atend. |
|---|---|---|---|---|---|
| 0 | Cafeteira Inicial | — | 0% | 0% | 0% |
| 1 | Cafeteira Polida | 300 🪙 | +5% | +5% | — |
| 2 | Caldeira Reforçada | 750 🪙 | +10% | +10% | — |
| 3 | Moedor Embutido | 1.500 🪙 | +15% | +15% | +5% |
| 4 | Máquina Profissional | 3.000 🪙 | +20% | +20% | +10% |
| 5 | **Luminepressa Deluxe** | 6.000 🪙 | +30% | +25% | +15% |

#### Preparo e Venda

| Comando | Aliases | Descrição |
|---|---|---|
| `l!cardapio` | `menu`, `cardápio`, `drinks`, `receitas` | Receitas públicas, preços e bebida do dia 📋 |
| `l!preparar <bebida> [qtd]` | `fazer`, `brew`, `prepara`, `make` | Prepara até 20 unidades de uma vez ☕ |
| `l!estoque` | `stock`, `inventory`, `inv`, `inventario` | Vê suas bebidas prontas 🧺 |
| `l!vender <bebida>` | `sell`, `venda`, `vende` | Vende 1 unidade do estoque 💰 |
| `l!inventar <ing1> <ing2> ...` | `experimentar`, `misturar`, `mix`, `experiment` | Combina ingredientes e descobre receitas secretas 🧪 |

**8 bebidas públicas:**

| Bebida | Receita | Venda | XP |
|---|---|---|---|
| ☕ Café Simples | Grão ×1 | 20 🪙 | +5 |
| 🧋 Cappuccino | Grão ×1, Leite ×1 | 35 🪙 | +10 |
| 🥤 Latte | Grão ×1, Leite ×2 | 45 🪙 | +12 |
| 🧊 Café Gelado | Grão ×1, Gelo ×2 | 30 🪙 | +14 |
| 🥛 Frappuccino | Grão ×1, Leite ×1, Gelo ×2, Chantilly ×1 | 70 🪙 | +20 |
| 🍯 Caramel Macchiato | Grão ×1, Leite ×1, Caramelo ×1 | 65 🪙 | +18 |
| 🍵 Matcha Latte | Matcha ×1, Leite ×2 | 75 🪙 | +17 |
| 🍫 Mocha | Grão ×1, Leite ×1, Chocolate ×1 | 65 🪙 | +17 |

**Bebida do dia:** uma bebida recebe bônus de **XP ao preparar** e **bônus no preço de venda** (determinístico por dia).

**Cooldown de preparação:** 5 minutos para a cafeteira "esfriar" entre usos.

#### Receitas Secretas

Ao descobrir uma receita pela primeira vez com `l!inventar`: **XP dobrado** + **100 Lumicoins de bônus**. Ingredientes são consumidos mesmo em tentativas erradas.

**15 receitas secretas** aguardando descoberta:

> 🧞‍♂️ Café das Arábias • ❄️ Mocha Branco de Inverno • 🍋 Cold Brew de Limão • 🌊 Café com Sal Marinho • 🍓 Frapê de Morango Selvagem • 🌸 Latte de Flor de Cerejeira • 🌿 Choconta • 🍪 Gingerbread Latte • 🥥 Cocoa Espresso • 👼 Lágrimas de Anjo • 🍯 Honey Citrus Tea • 🥶 Bomba de Gelo • 🌴 Café Cubano • 🎀 Pink Matcha • 💋 Beijo de Caramelo Salgado

**Sistema de pistas:** durante atendimentos e no `l!trabalhar`, a Lumine e os clientes NPC dão pistas narrativas sutis sobre receitas ainda não descobertas.

#### Atendimento de Clientes

| Comando | Aliases | Descrição |
|---|---|---|
| `l!atender` | `cliente`, `servir`, `serve`, `atend` | Recebe um novo cliente (cooldown: **60 min**) 👥 |
| `l!atender <bebida>` | — | Serve o cliente pendente **ou** "rouba" o cliente de outro barista |

- O cliente tem **5 minutos** para ser atendido antes de ir embora (e o cooldown continua contando).
- **15% de chance** de aparecer um **Cliente VIP** 👑 — recompensa maior (**80–220 🪙 + 15–40 XP**).
- **Mecânica de roubo:** se você tiver uma bebida que coincide com o pedido pendente de outro barista, pode atender o cliente dele primeiro e ganhar a recompensa.
- Atendimento normal rende **20–60 🪙 + 5–15 XP** (com bônus da cafeteira aplicado).

#### Troca de Ingredientes

| Comando | Aliases | Descrição |
|---|---|---|
| `l!trocar @user <ing> [qtd] por <ing> [qtd]` | `trade`, `troca`, `exchange`, `swap` | Propõe uma troca de ingredientes com outro barista 🤝 |

A outra pessoa recebe um embed interativo com botões de **Aceitar** ou **Recusar** (60 segundos para responder). A troca só ocorre se ambos tiverem os ingredientes no momento da confirmação.

#### Progressão de Barista (XP e Níveis)

| Nível | Título | XP necessário |
|---|---|---|
| 1 | Barista Novato ☕ | 0 |
| 2 | Barista Aprendiz ☕ | 100 |
| 3 | Barista Experiente ☕ | 300 |
| 4 | Barista Sênior 🌟 | 700 |
| 5 | Mestre Barista 🌟 | 1.500 |
| 6 | Lenda do Café 👑 | 3.000 |

#### Conquistas 🏆

| Comando | Aliases | Descrição |
|---|---|---|
| `l!conquistas` | `achievements`, `badges`, `badge` | Veja suas conquistas desbloqueadas |

**16 conquistas** desbloqueáveis automaticamente ao atingir marcos:

| Conquista | Condição |
|---|---|
| ☕ Primeiro Dia de Trabalho | Trabalhar pela 1ª vez |
| 💼 Incansável | Trabalhar 50 vezes |
| 🥤 Aprendiz de Barista | Preparar a 1ª bebida |
| 🏭 Linha de Produção | Preparar 100 bebidas no total |
| 📋 Conhecedor do Cardápio | Preparar todas as 8 bebidas públicas pelo menos 1 vez |
| 🧪 Alquimista | Descobrir 1 receita secreta |
| 📖 Meio Grimório | Descobrir 8 receitas secretas |
| 🔮 Grimório Completo | Descobrir todas as 15 receitas secretas |
| 👥 Bem-vindo ao Balcão! | Atender o 1º cliente |
| 🌆 O Barista da Cidade | Atender 100 clientes |
| 👑 Serviço de Primeira Classe | Atender um cliente VIP |
| 🏃 Oportunista | Roubar o cliente de outro barista |
| ✨ Luminepressa Deluxe | Atingir o nível máximo da cafeteira |
| 🌟 Mestre Barista | Atingir 1.500 XP |
| 👑 Lenda do Café | Atingir 3.000 XP |

---

### 🎮 Pokémon

Consulta a **PokéAPI** (gratuita, sem autenticação). Suporta os **1025 Pokémon** das Gerações I–IX.

| Comando | Aliases | Descrição |
|---|---|---|
| `l!pokemon` | `pokedex`, `pokédex`, `poke` | Curiosidade sobre um Pokémon **aleatório** 🎲 |
| `l!pokemon <nome>` | — | Busca por nome — ex: `l!pokemon charizard` |
| `l!pokemon <número>` | — | Busca por número — ex: `l!pokemon 006` |

O embed exibe:
- Número, nome, badge (🌟 Lendário / ✨ Mítico)
- Tipo(s) com emoji e **cor do embed por tipo primário** (18 cores)
- Geração (traduzida para PT — Gens I a IX)
- Peso e altura
- Habilidades normais e oculta
- Texto da Pokédex (sorteado entre as entradas dos jogos, **prioridade pt-BR**)
- Stats base com barra visual `█░` (HP, ATK, DEF, SpA, SpD, SPD + total)
- Artwork oficial como thumbnail

---

### 🎲 Dados

| Comando | Aliases | Descrição |
|---|---|---|
| `l!roll <expressão>` | `r`, `rolar` | Rola dados 🎲 |

**Formatos aceitos:**

| Formato | Exemplo | Descrição |
|---|---|---|
| `NdX` | `3d6` | N dados de X faces |
| `NdX+M` / `NdX-M` | `1d20+5` | Com modificador |
| `T#NdX+M` | `5#3d6+2` | Repete T vezes |

**Limites:** até 100 repetições, 100 dados, 10.000 faces.

> **✨ Atalho mágico:** mande **só** a expressão no chat (ex: `2d6`) e a Lumine rola automaticamente — sem precisar de `l!roll`! Funciona apenas quando a mensagem é somente a expressão.

---

### 💙 Help

| Comando | Aliases | Descrição |
|---|---|---|
| `l!help` | `ajuda`, `comandos` | Cardápio geral com todas as categorias |
| `l!help <categoria>` | — | Página detalhada de uma categoria |

Categorias disponíveis: `musica`, `dados`, `pokemon`, `cafe`.

O sistema é extensível: qualquer cog que implemente `help_meta()` e `help_field()` aparece automaticamente. Cogs podem injetar seções extras em outras categorias via `help_field_extra()` (exemplo: `playlists.py` injeta sua seção dentro de `l!help musica`).

A saudação e o título do `l!help` variam conforme o **período do dia**.

---

## 🌙 Sistema de Humor

A Lumine tem uma **personalidade dinâmica** que muda a cada **30 minutos** conforme o horário local:

| Período | Horário | Emoji | Exemplos de presença |
|---|---|---|---|
| Manhã | 05h–11h | 🌅 | "ouvindo os sons tranquilos da manhã" |
| Tarde | 12h–17h | ☕ | "competindo contra a preguiça da tarde" |
| Noite | 18h–22h | 🌙 | "assistindo às estrelas no céu" |
| Madrugada | 23h–04h | 🌌 | "tentando não dormir sentada" |

O humor afeta:
- **Status/presença** do bot no Discord (atualizado automaticamente)
- **Saudações** no `l!help`
- **Frases de pausa** e **canal vazio** no player de música
- **Frases de turno** no `l!trabalhar` do café
- **Footer** do embed "Tocando agora~"

---

## 🗂️ Estrutura do Projeto

```
Discord_LumineDLumiere/
├── core.py                  # Inicialização, Lavalink local, sistema de humor e carregamento de cogs
├── requirements.txt         # Dependências Python
├── .env                     # Tokens e segredos (não sobe pro Git!)
├── .env.example             # Modelo do arquivo .env
├── Procfile                 # Deploy em plataformas como Railway
│
├── cogs/                    # Módulos de funcionalidade (cada um é um Cog)
│   ├── __init__.py
│   ├── help.py              # Sistema de ajuda dinâmico e extensível (l!help)
│   ├── music.py             # Player de música via Lavalink/Wavelink
│   ├── playlists.py         # Playlists pessoais (l!pl save/list/show/add/...)
│   ├── dice.py              # Rolagem de dados RPG (l!roll + auto-detect)
│   ├── pokemon.py           # Consulta PokéAPI (l!pokemon)
│   └── cafe/                # Sistema de cafeteria (módulo dividido em camadas)
│       ├── __init__.py
│       ├── cog.py           # Comandos Discord do café (camada de apresentação)
│       ├── service.py       # Lógica de negócio pura (sem Discord, 100% testável)
│       ├── repository.py    # Persistência e acesso aos dados (JSON via JsonStore)
│       ├── catalog.py       # Catálogo: ingredientes, bebidas, receitas, upgrades, níveis
│       ├── narrative.py     # Textos: clientes NPC, pistas de receitas, frases
│       ├── conquistas.py    # Definição e verificação das conquistas
│       ├── images.py        # Busca de imagens de anime para embeds de clientes
│       └── daily.py         # Promoção diária e bebida do dia (determinístico por data)
│
├── utils/                   # Infraestrutura compartilhada
│   ├── __init__.py
│   ├── logging_setup.py     # Configuração do logger
│   ├── mood.py              # Sistema de humor por período do dia
│   ├── paths.py             # Caminhos absolutos para os arquivos de dados
│   └── storage.py           # JsonStore: leitura/escrita atômica com lock assíncrono
│
├── data/                    # Dados persistidos localmente (ignorados pelo Git)
│   ├── cafe_data.json        # Dados dos baristas (moedas, XP, ingredientes, etc.)
│   ├── cafe_data.example.json
│   ├── playlists.json        # Playlists salvas pelos usuários
│   └── playlists.example.json
│
├── tests/                   # Testes automatizados (pytest)
│
└── bin/                     # Lavalink e Java portátil
    ├── Lavalink.jar          # Baixe manualmente (não está no repositório)
    ├── application.yml       # Configuração do servidor Lavalink (não sobe pro Git!)
    ├── application.yml.example
    ├── jre/                  # Java 17 portátil (não está no repositório)
    └── plugins/              # Plugins do Lavalink (não estão no repositório)
```

---

## ⚙️ Arquitetura Interna

### Lavalink automático
O `core.py` verifica se a porta `2333` já está em uso. Se não estiver **e** `LAVALINK_MANAGED=true`, inicia o `Lavalink.jar` usando o Java portátil em `bin/jre/`. Ao encerrar o bot, o processo do Lavalink é terminado automaticamente. Para deploy remoto (Railway, etc.), use `LAVALINK_MANAGED=false`.

### JsonStore (`utils/storage.py`)
Abstração de persistência JSON com:
- **Lock assíncrono por arquivo** — sem corridas entre comandos simultâneos.
- **Escrita atômica** — salva em `.tmp` e substitui o arquivo original via `os.replace`.
- Métodos: `read()`, `replace()`.

### Sistema de Help extensível (`cogs/help.py`)
Cada cog expõe:
- `help_meta()` → chave, aliases, ícone, categoria, descrição curta.
- `help_field()` → título e corpo do campo detalhado.
- `help_field_extra()` *(opcional)* → injeta uma seção extra em outra categoria.

Busca é **case-insensitive e ignora acentos** (`música` = `musica`).

### Café — separação em camadas

| Camada | Arquivo | Responsabilidade |
|---|---|---|
| Apresentação | `cog.py` | Recebe comandos Discord, formata embeds, trata erros |
| Negócio | `service.py` | Lógica pura (sem Discord): trabalhar, comprar, preparar, inventar, vender, atender, roubar, trocar |
| Dados | `repository.py` | Lê/escreve `cafe_data.json`; coordena operações multi-usuário |
| Catálogo | `catalog.py` | Constantes: ingredientes, bebidas, receitas, upgrades, cooldowns |
| Conquistas | `conquistas.py` | Definição e verificação automática de todas as conquistas |
| Narrativa | `narrative.py` | Textos de clientes NPC, pistas de receitas, frases da Lumine |
| Imagens | `images.py` | Cache de imagens de anime para embeds de clientes |
| Diário | `daily.py` | Promoção e bebida do dia, determinísticas por semente da data |

### Tratamento global de erros (`core.py`)
- `CommandNotFound` → silencioso
- `MissingRequiredArgument` / `BadArgument` → mensagem educativa com dica de `l!help`
- `CheckFailure` → mensagem de permissão negada
- `CommandOnCooldown` → contador de segundos até liberar
- Erros inesperados → gera **código de rastreamento hexadecimal** e loga com stack trace completo

---

## 🚀 Como Rodar

### Pré-requisitos

- Python **3.11+**
- Java **17** (portátil em `bin/jre/` **ou** instalado no sistema)
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
cp .env.example .env
# Edite o .env e preencha os valores

# 5. Configure o Lavalink (se for rodar localmente)
cp bin/application.yml.example bin/application.yml
```

### Configuração (`.env`)

```env
# Obrigatório
DISCORD_TOKEN=seu_token_aqui

# Lavalink
LAVALINK_URI=http://127.0.0.1:2333
LAVALINK_PASSWORD=youshallnotpass
LAVALINK_MANAGED=true          # false para Railway/servidor com Lavalink externo

# YouTube OAuth (opcional — para contornar bloqueios do YouTube no Lavalink)
YOUTUBE_REFRESH_TOKEN=

# Spotify (desativado atualmente)
SPOTIFY_CLIENT_ID=
SPOTIFY_CLIENT_SECRET=
```

### Execução

```bash
python core.py
```

O bot inicializa o Lavalink automaticamente (se `bin/Lavalink.jar` e `bin/jre/` existirem e `LAVALINK_MANAGED=true`) e carrega todos os cogs. O Lavalink é encerrado junto com o bot.

---

## 📦 Dependências

```
discord.py[voice]==2.5.2    # biblioteca principal do Discord
python-dotenv==1.1.1        # carregamento do .env
wavelink==3.4.1             # wrapper para o servidor Lavalink
aiohttp==3.12.13            # HTTP client (usado no Pokémon e imagens do café)
```

Dependências de desenvolvimento (pytest, ruff) estão em `requirements-dev.txt`.

---

## 🔒 Segurança e Git

Os seguintes arquivos **nunca sobem** para o repositório (`.gitignore`):

| Arquivo / Pasta | Motivo |
|---|---|
| `.env` | Token do bot e segredos |
| `bin/application.yml` | Configuração do Lavalink com senha |
| `bin/Lavalink.jar` | Binário pesado (~96 MB) |
| `bin/jre/` | Java portátil (~200 MB) |
| `bin/plugins/` | Plugins do Lavalink |
| `data/*.json` | Dados de usuários (privacidade) |
| `venv/` | Ambiente virtual Python |

Use os arquivos `.example` como base para configuração local.

---

## 🎀 Persona da Lumine

A Lumine D'Lumière é uma maid virtual com personalidade carinhosa e fofa. Características:
- Usa expressões como `~`, `💙`, `✨`, `🥺` nas mensagens.
- Personalidade contextual: mais animada de tarde, mais quietinha na madrugada.
- Clientes NPC com personalidades distintas: falas únicas de pedido, agradecimento, recusa e atendimento roubado.
- Sistema de pistas de receitas narrado de forma poética e indireta pela Lumine e pelos clientes.
- Mensagens de canal vazio e pausa personalizadas por período do dia.

---

*Feito com 💙 e muito café.*
