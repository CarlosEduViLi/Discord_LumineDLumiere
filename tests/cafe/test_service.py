"""
tests/cafe/test_service.py
Testes unitários de cogs/cafe/service.py.

Cobre: trabalhar, comprar, preparar, inventar, vender,
iniciar_atendimento, servir_atendimento, roubar_atendimento,
dar_moedas, executar_troca e funções utilitárias.

Usa RNG e clock injetáveis para testes 100% determinísticos.
"""
from __future__ import annotations

import time
from typing import Any

from cogs.cafe.catalog import (
    BEBIDAS,
    CD_ATENDER,
    CD_TRABALHAR,
    INGREDIENTES,
    RECEITAS_SECRETAS,
)
from cogs.cafe.service import (
    comprar,
    cooldown_restante,
    dar_moedas,
    default_user,
    executar_troca,
    formatar_tempo,
    iniciar_atendimento,
    inventar,
    normalizar_bebida,
    normalizar_ingrediente,
    normalizar_texto,
    parse_ingredient_sequence,
    parse_purchase_tokens,
    preparar,
    roubar_atendimento,
    servir_atendimento,
    trabalhar,
    vender,
)

# ---------------------------------------------------------------------------
# Fixtures / Helpers
# ---------------------------------------------------------------------------

class FixedRng:
    """RNG determinístico para testes: sempre retorna o primeiro elemento."""

    def __init__(self, choice_result: Any = None, randint_result: int = 50):
        self._choice_result = choice_result
        self._randint_result = randint_result

    def choice(self, seq):
        if self._choice_result is not None:
            return self._choice_result
        return seq[0]

    def randint(self, a: int, b: int) -> int:
        return max(a, min(b, self._randint_result))


def make_user(**kwargs) -> dict:
    """Cria usuário com defaults, permitindo sobrescritas."""
    u = default_user()
    u.update(kwargs)
    return u


def user_com_moedas(n: int) -> dict:
    return make_user(lumicoins=n)


def user_com_ingredientes(**ingredientes) -> dict:
    return make_user(lumicoins=500, ingredientes=dict(ingredientes))


def user_com_estoque(**estoque) -> dict:
    return make_user(lumicoins=200, estoque=dict(estoque))


AGORA = 1_000_000.0  # timestamp fixo para testes


# ---------------------------------------------------------------------------
# normalizar_texto / normalizar_ingrediente / normalizar_bebida
# ---------------------------------------------------------------------------

class TestNormalizarTexto:
    def test_remove_acentos(self):
        assert normalizar_texto("Açúcar") == "acucar"

    def test_espacos_viram_underscore(self):
        assert normalizar_texto("leite condensado") == "leite_condensado"

    def test_maiusculas_viram_minusculas(self):
        assert normalizar_texto("MATCHA") == "matcha"

    def test_cifrao_removido(self):
        assert normalizar_texto("$grao") == "grao"

    def test_hifens_viram_underscore(self):
        assert normalizar_texto("café-gelado") == "cafe_gelado"


class TestNormalizarIngrediente:
    def test_alias_graos(self):
        assert normalizar_ingrediente("grãos") == "grao"

    def test_alias_leite_condensado(self):
        assert normalizar_ingrediente("leite condensado") == "leite_cond"

    def test_alias_invalido_retorna_none(self):
        assert normalizar_ingrediente("carne") is None

    def test_alias_flor_cerejeira(self):
        assert normalizar_ingrediente("flor de cerejeira") == "sakura"


class TestNormalizarBebida:
    def test_alias_cafe(self):
        assert normalizar_bebida("café") == "cafe_simples"

    def test_alias_macchiato(self):
        assert normalizar_bebida("macchiato") == "caramel_macchiato"

    def test_chave_existente(self):
        assert normalizar_bebida("cappuccino") == "cappuccino"

    def test_desconhecido_retorna_normalizado(self):
        assert normalizar_bebida("bebida inexistente") == "bebida_inexistente"


# ---------------------------------------------------------------------------
# cooldown_restante / formatar_tempo
# ---------------------------------------------------------------------------

class TestCooldownRestante:
    def test_sem_cooldown(self):
        assert cooldown_restante(0.0, CD_TRABALHAR, agora=AGORA) == 0.0

    def test_cooldown_ativo(self):
        cd = cooldown_restante(AGORA, CD_TRABALHAR, agora=AGORA + 60)
        assert cd == CD_TRABALHAR - 60

    def test_cooldown_expirado(self):
        cd = cooldown_restante(AGORA - CD_TRABALHAR - 1, CD_TRABALHAR, agora=AGORA)
        assert cd == 0.0


class TestFormatarTempo:
    def test_menos_de_um_minuto(self):
        assert formatar_tempo(45) == "45s"

    def test_exatamente_um_minuto(self):
        assert formatar_tempo(60) == "1min"

    def test_minutos_e_segundos(self):
        assert formatar_tempo(90) == "1min 30s"

    def test_varios_minutos(self):
        assert formatar_tempo(3600) == "60min"


# ---------------------------------------------------------------------------
# parse_purchase_tokens
# ---------------------------------------------------------------------------

class TestParsePurchaseTokens:
    def test_ingrediente_valido(self):
        r = parse_purchase_tokens(["grao", "3"])
        assert r["ok"] is True
        assert r["pedidos"]["grao"] == 3

    def test_sem_quantidade_usa_1(self):
        r = parse_purchase_tokens(["leite"])
        assert r["ok"] is True
        assert r["pedidos"]["leite"] == 1

    def test_ingrediente_invalido(self):
        r = parse_purchase_tokens(["abacaxi"])
        assert r["ok"] is False
        assert r["reason"] == "ingrediente_invalido"

    def test_lista_vazia(self):
        r = parse_purchase_tokens([])
        assert r["ok"] is False
        assert r["reason"] == "vazio"

    def test_quantidade_maxima_excedida(self):
        r = parse_purchase_tokens(["grao", "100"])
        assert r["ok"] is False
        assert r["reason"] == "quantidade_maxima"

    def test_multiplos_ingredientes(self):
        r = parse_purchase_tokens(["grao", "2", "leite", "3"])
        assert r["ok"] is True
        assert r["pedidos"] == {"grao": 2, "leite": 3}

    def test_alias_dois_tokens(self):
        r = parse_purchase_tokens(["leite", "condensado", "2"])
        assert r["ok"] is True
        assert r["pedidos"]["leite_cond"] == 2


# ---------------------------------------------------------------------------
# parse_ingredient_sequence
# ---------------------------------------------------------------------------

class TestParseIngredientSequence:
    def test_minimo_dois_ingredientes(self):
        r = parse_ingredient_sequence(["grao"])
        assert r["ok"] is False
        assert r["reason"] == "minimo_ingredientes"

    def test_dois_ingredientes_validos(self):
        r = parse_ingredient_sequence(["grao", "leite"])
        assert r["ok"] is True
        assert r["tentativa"] == {"grao": 1, "leite": 1}

    def test_ingrediente_invalido(self):
        r = parse_ingredient_sequence(["grao", "pizza"])
        assert r["ok"] is False
        assert r["reason"] == "ingrediente_invalido"

    def test_repetido_acumula(self):
        r = parse_ingredient_sequence(["grao", "grao"])
        assert r["ok"] is True
        assert r["tentativa"]["grao"] == 2


# ---------------------------------------------------------------------------
# trabalhar
# ---------------------------------------------------------------------------

class TestTrabalhar:
    def test_sucesso(self):
        user = user_com_moedas(0)
        rng = FixedRng(randint_result=50)
        r = trabalhar(user, agora=AGORA, rng=rng)
        assert r["ok"] is True
        assert r["ganho"] == 50
        assert r["user"]["lumicoins"] == 50
        assert r["user"]["stats"]["trabalhos"] == 1

    def test_cooldown_ativo(self):
        user = make_user(cd_trabalhar=AGORA)
        r = trabalhar(user, agora=AGORA + 60)
        assert r["ok"] is False
        assert r["reason"] == "cooldown"
        assert r["cooldown"] > 0

    def test_cooldown_expirado_permite_trabalho(self):
        user = make_user(cd_trabalhar=AGORA - CD_TRABALHAR - 1)
        r = trabalhar(user, agora=AGORA)
        assert r["ok"] is True

    def test_nao_muta_user_original(self):
        user = user_com_moedas(0)
        original_coins = user["lumicoins"]
        trabalhar(user, agora=AGORA)
        assert user["lumicoins"] == original_coins

    def test_conquista_primeiro_turno(self):
        user = user_com_moedas(0)
        r = trabalhar(user, agora=AGORA)
        assert "primeiro_turno" in r["conquistas_novas"]


# ---------------------------------------------------------------------------
# comprar
# ---------------------------------------------------------------------------

class TestComprar:
    def test_sucesso(self, monkeypatch):
        # Neutraliza o desconto diário para que o preço seja sempre o base do catálogo.
        monkeypatch.setattr("cogs.cafe.service.get_categoria_desconto", lambda: "")
        monkeypatch.setattr("cogs.cafe.service.get_desconto_pct", lambda: 0)
        user = user_com_moedas(500)
        r = comprar(user, ["grao", "5"])
        assert r["ok"] is True
        assert r["user"]["ingredientes"]["grao"] == 5
        assert r["user"]["lumicoins"] == 500 - (INGREDIENTES["grao"]["preco"] * 5)

    def test_saldo_insuficiente(self):
        user = user_com_moedas(1)
        r = comprar(user, ["grao", "99"])
        assert r["ok"] is False
        assert r["reason"] == "saldo_insuficiente"

    def test_ingrediente_invalido(self):
        user = user_com_moedas(500)
        r = comprar(user, ["pizza"])
        assert r["ok"] is False
        assert r["reason"] == "ingrediente_invalido"

    def test_acumula_ingrediente_existente(self):
        user = make_user(lumicoins=500, ingredientes={"grao": 3})
        r = comprar(user, ["grao", "2"])
        assert r["ok"] is True
        assert r["user"]["ingredientes"]["grao"] == 5

    def test_nao_muta_user_original(self):
        user = user_com_moedas(500)
        comprar(user, ["grao", "1"])
        assert user["lumicoins"] == 500

    def test_tokens_vazios(self):
        user = user_com_moedas(500)
        r = comprar(user, [])
        assert r["ok"] is False

    def test_multiplos_ingredientes(self):
        user = user_com_moedas(1000)
        r = comprar(user, ["grao", "2", "leite", "1"])
        assert r["ok"] is True
        assert r["user"]["ingredientes"]["grao"] == 2
        assert r["user"]["ingredientes"]["leite"] == 1


# ---------------------------------------------------------------------------
# preparar
# ---------------------------------------------------------------------------

class TestPreparar:
    def test_sucesso_cafe_simples(self):
        user = user_com_ingredientes(grao=1)
        r = preparar(user, "cafe_simples")
        assert r["ok"] is True
        assert r["bebida"] == "cafe_simples"
        assert r["user"]["estoque"].get("cafe_simples", 0) == 1
        assert r["user"]["ingredientes"].get("grao", 0) == 0
        assert r["xp_ganho"] > 0

    def test_ingredientes_insuficientes(self):
        user = user_com_ingredientes()  # sem ingredientes
        r = preparar(user, "cafe_simples")
        assert r["ok"] is False
        assert r["reason"] == "ingredientes_insuficientes"

    def test_bebida_invalida(self):
        user = user_com_ingredientes(grao=5)
        r = preparar(user, "bebida_magica")
        assert r["ok"] is False
        assert r["reason"] == "bebida_invalida"

    def test_quantidade_multipla(self):
        user = user_com_ingredientes(grao=3)
        r = preparar(user, "cafe_simples", quantidade=3)
        assert r["ok"] is True
        assert r["quantidade"] == 3
        assert r["user"]["estoque"]["cafe_simples"] == 3
        assert r["user"]["ingredientes"].get("grao", 0) == 0

    def test_quantidade_limite_maximo_20(self):
        user = user_com_ingredientes(grao=100)
        r = preparar(user, "cafe_simples", quantidade=50)
        assert r["ok"] is True
        assert r["quantidade"] == 20  # limitado a 20

    def test_ingrediente_zerado_removido(self):
        user = user_com_ingredientes(grao=1, leite=1)
        preparar(user, "cafe_simples")  # usa apenas grao
        preparar(user, "cafe_simples")
        # User original não é mutado; verificamos via resultado
        r2 = preparar(user, "cafe_simples")
        assert "grao" not in r2["user"]["ingredientes"]

    def test_nao_muta_user_original(self):
        user = user_com_ingredientes(grao=5)
        preparar(user, "cafe_simples")
        assert user["ingredientes"]["grao"] == 5

    def test_conquista_primeira_bebida(self):
        user = user_com_ingredientes(grao=1)
        r = preparar(user, "cafe_simples")
        assert "primeira_bebida" in r["conquistas_novas"]

    def test_receita_secreta_nao_disponivel_sem_desbloqueio(self):
        """Receitas secretas não devem aparecer sem desbloqueio."""
        user = make_user(lumicoins=500, ingredientes={"grao": 1, "canela": 1, "pimenta": 1})
        r = preparar(user, "cafe_arabias")
        assert r["ok"] is False  # não está no catálogo sem desbloqueio


# ---------------------------------------------------------------------------
# inventar
# ---------------------------------------------------------------------------

class TestInventar:
    def _user_com_receita(self, chave: str) -> dict:
        """Cria usuário com todos os ingredientes de uma receita secreta."""
        receita = RECEITAS_SECRETAS[chave]["receita"]
        return make_user(lumicoins=200, ingredientes=dict(receita))

    def test_receita_correta_desbloqueia(self):
        user = self._user_com_receita("cafe_arabias")
        r = inventar(user, ["grao", "canela", "pimenta"])
        assert r["ok"] is True
        assert r["acertou"] is True
        assert r["bebida"] == "cafe_arabias"
        assert not r["ja_desbloqueada"]
        assert r["xp_ganho"] == RECEITAS_SECRETAS["cafe_arabias"]["xp"] * 2  # bônus primeira vez

    def test_receita_ja_desbloqueada_sem_bonus_duplo(self):
        user = self._user_com_receita("cafe_arabias")
        user["receitas_desbloqueadas"] = ["cafe_arabias"]
        user["estoque"]["cafe_arabias"] = 1  # já tem no estoque
        r = inventar(user, ["grao", "canela", "pimenta"])
        assert r["ok"] is True
        assert r["ja_desbloqueada"] is True
        assert r["xp_ganho"] == RECEITAS_SECRETAS["cafe_arabias"]["xp"]  # sem bônus

    def test_tentativa_errada_nao_acerta(self):
        user = make_user(ingredientes={"grao": 1, "leite": 1})
        r = inventar(user, ["grao", "leite"])
        assert r["ok"] is True
        assert r["acertou"] is False

    def test_ingredientes_insuficientes(self):
        user = make_user(ingredientes={"grao": 0})
        r = inventar(user, ["grao", "canela"])
        assert r["ok"] is False
        assert r["reason"] == "ingredientes_insuficientes"

    def test_minimo_dois_ingredientes(self):
        user = make_user(ingredientes={"grao": 1})
        r = inventar(user, ["grao"])
        assert r["ok"] is False
        assert r["reason"] == "minimo_ingredientes"

    def test_ingrediente_invalido(self):
        user = make_user(ingredientes={"grao": 1})
        r = inventar(user, ["grao", "abacaxi"])
        assert r["ok"] is False
        assert r["reason"] == "ingrediente_invalido"

    def test_conquista_primeira_descoberta(self):
        user = self._user_com_receita("cafe_arabias")
        r = inventar(user, ["grao", "canela", "pimenta"])
        assert r["ok"] is True
        assert "primeira_descoberta" in r["conquistas_novas"]

    def test_nao_muta_user_original(self):
        user = self._user_com_receita("cafe_arabias")
        ing_antes = dict(user["ingredientes"])
        inventar(user, ["grao", "canela", "pimenta"])
        assert user["ingredientes"] == ing_antes


# ---------------------------------------------------------------------------
# vender
# ---------------------------------------------------------------------------

class TestVender:
    def test_sucesso(self):
        user = user_com_estoque(cafe_simples=1)
        r = vender(user, "cafe_simples")
        assert r["ok"] is True
        assert r["user"]["lumicoins"] == 200 + BEBIDAS["cafe_simples"]["preco_venda"]
        assert r["user"]["estoque"].get("cafe_simples", 0) == 0

    def test_sem_estoque(self):
        user = user_com_estoque()
        r = vender(user, "cafe_simples")
        assert r["ok"] is False
        assert r["reason"] == "sem_estoque"

    def test_bebida_invalida(self):
        user = user_com_estoque(cafe_simples=1)
        r = vender(user, "bebida_magica")
        assert r["ok"] is False
        assert r["reason"] == "bebida_invalida"

    def test_nao_muta_user_original(self):
        user = user_com_estoque(cafe_simples=2)
        coins_antes = user["lumicoins"]
        vender(user, "cafe_simples")
        assert user["lumicoins"] == coins_antes

    def test_estoque_zerado_remove_chave(self):
        user = user_com_estoque(cafe_simples=1)
        r = vender(user, "cafe_simples")
        assert "cafe_simples" not in r["user"]["estoque"]


# ---------------------------------------------------------------------------
# iniciar_atendimento
# ---------------------------------------------------------------------------

class TestIniciarAtendimento:
    def test_novo_cliente(self):
        user = user_com_moedas(200)
        # Usamos randint=20 => não VIP (20 > VIP_CHANCE=15)
        rng2 = FixedRng(randint_result=20)
        r = iniciar_atendimento(user, agora=AGORA, rng=rng2)
        assert r["ok"] is True
        assert r["status"] == "novo"
        assert "cliente_pendente" in r["user"]
        assert r["user"]["cliente_pendente"]["bebida"] is not None

    def test_cooldown_ativo(self):
        user = make_user(cd_atender=AGORA)
        r = iniciar_atendimento(user, agora=AGORA + 60)
        assert r["ok"] is False
        assert r["reason"] == "cooldown"

    def test_cliente_pendente_nao_expirado_retorna_pendente(self):
        user = make_user(
            cd_atender=AGORA - CD_ATENDER - 1,
            cliente_pendente={"cliente": "Diluc", "bebida": "cafe_simples", "ts": time.time(), "vip": False},
        )
        r = iniciar_atendimento(user, agora=AGORA + 60)  # 60s < CD_CLIENTE (300s)
        assert r["ok"] is True
        assert r["status"] == "pendente"

    def test_cliente_expirado_limpa_e_gera_cooldown(self):
        ts_antigo = time.time() - 400  # CD_CLIENTE = 300s, logo expirado
        user = make_user(
            cd_atender=AGORA - CD_ATENDER - 1,
            cliente_pendente={"cliente": "Diluc", "bebida": "cafe_simples", "ts": ts_antigo, "vip": False},
        )
        r = iniciar_atendimento(user, agora=AGORA, rng=FixedRng(randint_result=20))
        # Cliente expirado: limpa e gera novo se CD_ATENDER passou
        assert r["ok"] is True

    def test_cliente_vip_gerado(self):
        user = make_user(cd_atender=0)
        rng = FixedRng(randint_result=1)  # 1 <= VIP_CHANCE => VIP
        r = iniciar_atendimento(user, agora=AGORA, rng=rng)
        assert r["ok"] is True
        assert r["vip"] is True


# ---------------------------------------------------------------------------
# servir_atendimento
# ---------------------------------------------------------------------------

class TestServirAtendimento:
    def _user_com_cliente(self, bebida: str = "cafe_simples", vip: bool = False) -> dict:
        # Usa time.time() atual para o ts do cliente, garantindo que nao expire nos testes
        agora_real = time.time()
        return make_user(
            lumicoins=200,
            estoque={bebida: 1},
            cd_atender=agora_real,
            cliente_pendente={
                "cliente": "Fischl",
                "bebida": bebida,
                "ts": agora_real,
                "vip": vip,
            },
        )

    def test_sucesso(self):
        user = self._user_com_cliente("cafe_simples")
        r = servir_atendimento(user, "cafe_simples")
        assert r["ok"] is True
        assert r["status"] == "sucesso"
        assert r["user"]["lumicoins"] > 200
        assert "cliente_pendente" not in r["user"]

    def test_sem_cliente(self):
        user = user_com_moedas(200)
        r = servir_atendimento(user, "cafe_simples")
        assert r["ok"] is False
        assert r["reason"] == "sem_cliente"

    def test_bebida_errada(self):
        user = self._user_com_cliente("cafe_simples")
        user["estoque"]["cappuccino"] = 1
        r = servir_atendimento(user, "cappuccino")
        assert r["ok"] is True
        assert r["status"] == "erro"
        assert r["motivo"] == "bebida_errada"

    def test_sem_estoque_da_bebida_correta(self):
        user = self._user_com_cliente("cafe_simples")
        del user["estoque"]["cafe_simples"]  # remove o estoque
        r = servir_atendimento(user, "cafe_simples")
        assert r["ok"] is True
        assert r["status"] == "erro"
        assert r["motivo"] == "sem_estoque"

    def test_cliente_expirado(self):
        ts_antigo = time.time() - 400  # CD_CLIENTE=300s, logo expirado
        user = make_user(
            estoque={"cafe_simples": 1},
            cliente_pendente={
                "cliente": "Fischl", "bebida": "cafe_simples", "ts": ts_antigo, "vip": False,
            },
        )
        r = servir_atendimento(user, "cafe_simples")
        assert r["ok"] is False
        assert r["reason"] == "cliente_expirado"

    def test_conquista_primeiro_cliente(self):
        user = self._user_com_cliente("cafe_simples")
        r = servir_atendimento(user, "cafe_simples")
        assert "primeiro_cliente" in r["conquistas_novas"]

    def test_vip_da_mais_moedas(self):
        user_normal = self._user_com_cliente("cafe_simples", vip=False)
        user_vip = self._user_com_cliente("cafe_simples", vip=True)
        rng = FixedRng(randint_result=150)
        r_normal = servir_atendimento(user_normal, "cafe_simples", rng=rng)
        r_vip = servir_atendimento(user_vip, "cafe_simples", rng=rng)
        assert r_vip["bonus_moedas"] >= r_normal["bonus_moedas"]


# ---------------------------------------------------------------------------
# roubar_atendimento
# ---------------------------------------------------------------------------

class TestRoubarAtendimento:
    def _candidato(self, user_id: str, bebida: str) -> tuple:
        # Usa time.time() atual para que o cliente nao expire durante o teste
        agora_real = time.time()
        user = make_user(
            cd_atender=agora_real,
            estoque={bebida: 1},
            cliente_pendente={"cliente": "Kaeya", "bebida": bebida, "ts": agora_real, "vip": False},
        )
        return (user_id, user)

    def test_roubo_bem_sucedido(self):
        ladrão = make_user(lumicoins=200, estoque={"cafe_simples": 1})
        candidatos = [self._candidato("999", "cafe_simples")]
        r = roubar_atendimento(ladrão, "cafe_simples", candidatos)
        assert r["ok"] is True
        assert r["status"] == "roubo"
        assert r["user"]["stats"]["roubos"] == 1

    def test_sem_candidato_roubavel(self):
        ladrão = make_user(lumicoins=200, estoque={"cafe_simples": 1})
        candidatos = [self._candidato("999", "cappuccino")]  # tem cliente pedindo cappuccino
        r = roubar_atendimento(ladrão, "cafe_simples", candidatos)
        assert r["ok"] is False
        assert r["reason"] == "sem_cliente_roubavel"

    def test_com_cliente_proprio_pendente(self):
        ladrão = make_user(
            estoque={"cafe_simples": 1},
            cliente_pendente={"cliente": "X", "bebida": "cafe_simples", "ts": time.time(), "vip": False},
        )
        candidatos = [self._candidato("999", "cafe_simples")]
        r = roubar_atendimento(ladrão, "cafe_simples", candidatos)
        assert r["ok"] is False
        assert r["reason"] == "cliente_proprio_pendente"

    def test_sem_estoque(self):
        ladrão = make_user(lumicoins=200, estoque={})
        candidatos = [self._candidato("999", "cafe_simples")]
        r = roubar_atendimento(ladrão, "cafe_simples", candidatos)
        assert r["ok"] is False
        assert r["reason"] == "sem_estoque"

    def test_candidato_expirado_ignorado(self):
        ladrão = make_user(lumicoins=200, estoque={"cafe_simples": 1})
        ts_expirado = time.time() - 400  # CD_CLIENTE=300s, logo expirado
        alvo = make_user(
            cd_atender=time.time(),
            cliente_pendente={"cliente": "X", "bebida": "cafe_simples", "ts": ts_expirado, "vip": False},
        )
        candidatos = [("999", alvo)]
        r = roubar_atendimento(ladrão, "cafe_simples", candidatos)
        assert r["ok"] is False
        assert r["reason"] == "sem_cliente_roubavel"

    def test_conquista_oportunista(self):
        ladrão = make_user(lumicoins=200, estoque={"cafe_simples": 1})
        candidatos = [self._candidato("999", "cafe_simples")]
        r = roubar_atendimento(ladrão, "cafe_simples", candidatos)
        assert "oportunista" in r["conquistas_novas"]


# ---------------------------------------------------------------------------
# dar_moedas
# ---------------------------------------------------------------------------

class TestDarMoedas:
    def test_sucesso(self):
        sender = user_com_moedas(100)
        receiver = user_com_moedas(50)
        r = dar_moedas(sender, receiver, 30)
        assert r["ok"] is True
        assert r["user_sender"]["lumicoins"] == 70
        assert r["user_receiver"]["lumicoins"] == 80

    def test_saldo_insuficiente(self):
        sender = user_com_moedas(10)
        receiver = user_com_moedas(50)
        r = dar_moedas(sender, receiver, 100)
        assert r["ok"] is False
        assert r["reason"] == "saldo_insuficiente"

    def test_quantidade_invalida(self):
        sender = user_com_moedas(100)
        receiver = user_com_moedas(50)
        r = dar_moedas(sender, receiver, 0)
        assert r["ok"] is False
        assert r["reason"] == "quantidade_invalida"

    def test_nao_muta_originais(self):
        sender = user_com_moedas(100)
        receiver = user_com_moedas(50)
        dar_moedas(sender, receiver, 30)
        assert sender["lumicoins"] == 100
        assert receiver["lumicoins"] == 50

    def test_transferencia_total(self):
        sender = user_com_moedas(100)
        receiver = user_com_moedas(0)
        r = dar_moedas(sender, receiver, 100)
        assert r["ok"] is True
        assert r["user_sender"]["lumicoins"] == 0
        assert r["user_receiver"]["lumicoins"] == 100


# ---------------------------------------------------------------------------
# executar_troca
# ---------------------------------------------------------------------------

class TestExecutarTroca:
    def test_sucesso(self):
        a = make_user(ingredientes={"grao": 3})
        b = make_user(ingredientes={"leite": 2})
        r = executar_troca(a, b, "grao", 2, "leite", 1)
        assert r["ok"] is True
        assert r["user_a"]["ingredientes"]["grao"] == 1
        assert r["user_a"]["ingredientes"]["leite"] == 1
        assert r["user_b"]["ingredientes"]["leite"] == 1
        assert r["user_b"]["ingredientes"]["grao"] == 2

    def test_ingrediente_invalido_a(self):
        a = make_user()
        b = make_user()
        r = executar_troca(a, b, "abacaxi", 1, "leite", 1)
        assert r["ok"] is False
        assert r["reason"] == "ingrediente_invalido"

    def test_ingrediente_invalido_b(self):
        a = make_user(ingredientes={"grao": 1})
        b = make_user()
        r = executar_troca(a, b, "grao", 1, "pizza", 1)
        assert r["ok"] is False
        assert r["reason"] == "ingrediente_invalido"

    def test_sem_ingrediente_a(self):
        a = make_user(ingredientes={"grao": 0})
        b = make_user(ingredientes={"leite": 1})
        r = executar_troca(a, b, "grao", 1, "leite", 1)
        assert r["ok"] is False
        assert r["reason"] == "sem_ingredientes_a"

    def test_sem_ingrediente_b(self):
        a = make_user(ingredientes={"grao": 1})
        b = make_user(ingredientes={"leite": 0})
        r = executar_troca(a, b, "grao", 1, "leite", 1)
        assert r["ok"] is False
        assert r["reason"] == "sem_ingredientes_b"

    def test_nao_muta_originais(self):
        a = make_user(ingredientes={"grao": 3})
        b = make_user(ingredientes={"leite": 2})
        executar_troca(a, b, "grao", 1, "leite", 1)
        assert a["ingredientes"]["grao"] == 3
        assert b["ingredientes"]["leite"] == 2

    def test_ingrediente_zerado_removido(self):
        a = make_user(ingredientes={"grao": 1})
        b = make_user(ingredientes={"leite": 1})
        r = executar_troca(a, b, "grao", 1, "leite", 1)
        assert r["ok"] is True
        assert "grao" not in r["user_a"]["ingredientes"]
        assert "leite" not in r["user_b"]["ingredientes"]
