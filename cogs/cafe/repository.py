from __future__ import annotations

import copy
from collections.abc import Callable

from utils.paths import CAFE_DATA_PATH
from utils.storage import JsonStore

from .service import dar_moedas as _dar_moedas, executar_troca as _executar_troca, normalizar_user_data, roubar_atendimento, servir_atendimento


class CafeRepository:
    def __init__(self, store: JsonStore | None = None):
        self.store = store or JsonStore(CAFE_DATA_PATH)

    @staticmethod
    def _ensure_user(data: dict, guild_id: int, user_id: int) -> dict:
        guild = data.setdefault(str(guild_id), {})
        user = normalizar_user_data(guild.get(str(user_id)))
        guild[str(user_id)] = user
        return user

    async def get_user(self, guild_id: int, user_id: int) -> dict:
        def mutator(data: dict) -> dict:
            return copy.deepcopy(self._ensure_user(data, guild_id, user_id))

        return await self.store.update(mutator)

    async def update_user(self, guild_id: int, user_id: int, handler: Callable[[dict], dict]) -> dict:
        def mutator(data: dict) -> dict:
            user = copy.deepcopy(self._ensure_user(data, guild_id, user_id))
            result = handler(user)
            if "user" in result:
                data[str(guild_id)][str(user_id)] = normalizar_user_data(result["user"])
            return result

        return await self.store.update(mutator)

    async def atender_com_roubo(self, guild_id: int, user_id: int, bebida: str) -> dict:
        def mutator(data: dict) -> dict:
            guild = data.setdefault(str(guild_id), {})
            author_key = str(user_id)
            user = copy.deepcopy(self._ensure_user(data, guild_id, user_id))

            if user.get("cliente_pendente"):
                result = servir_atendimento(user, bebida)
                if "user" in result:
                    guild[author_key] = normalizar_user_data(result["user"])
                return result

            candidatos = [
                (other_id, other_data)
                for other_id, other_data in guild.items()
                if other_id != author_key and isinstance(other_data, dict)
            ]
            result = roubar_atendimento(user, bebida, candidatos)
            if result["ok"] and result.get("status") == "roubo":
                guild[author_key] = normalizar_user_data(result["user"])
                guild[str(result["alvo_id"])] = normalizar_user_data(result["alvo_user"])
            return result

        return await self.store.update(mutator)

    async def get_all_users(self, guild_id: int) -> dict[str, dict]:
        data = await self.store.read()
        guild = data.get(str(guild_id), {})
        return {
            user_id: normalizar_user_data(user_data)
            for user_id, user_data in guild.items()
            if isinstance(user_data, dict)
        }

    async def set_client_channel_id(self, guild_id: int, user_id: int, channel_id: int) -> None:
        """Armazena o canal em que o cliente chegou para o background task de timeout."""
        def mutator(data: dict) -> None:
            guild = data.get(str(guild_id), {})
            user = guild.get(str(user_id))
            if isinstance(user, dict) and isinstance(user.get("cliente_pendente"), dict):
                user["cliente_pendente"]["channel_id"] = channel_id
        await self.store.update(mutator)

    async def get_all_pending_clients(self) -> list[tuple[int, int, dict]]:
        """Retorna lista de (guild_id, user_id, cliente_pendente) para todos os usuários com cliente esperando."""
        data = await self.store.read()
        resultado = []
        for guild_id_str, guild_data in data.items():
            if not isinstance(guild_data, dict):
                continue
            for user_id_str, user_data in guild_data.items():
                if not isinstance(user_data, dict):
                    continue
                pendente = user_data.get("cliente_pendente")
                if isinstance(pendente, dict):
                    resultado.append((int(guild_id_str), int(user_id_str), pendente))
        return resultado

    async def remover_cliente_pendente(self, guild_id: int, user_id: int) -> None:
        """Remove atomicamente o cliente_pendente de um usuário."""
        def mutator(data: dict) -> None:
            guild = data.get(str(guild_id), {})
            user = guild.get(str(user_id))
            if isinstance(user, dict):
                user.pop("cliente_pendente", None)
        await self.store.update(mutator)

    async def dar_moedas(self, guild_id: int, sender_id: int, receiver_id: int, quantidade: int) -> dict:
        def mutator(data: dict) -> dict:
            gid = str(guild_id)
            data.setdefault(gid, {})
            sender = copy.deepcopy(self._ensure_user(data, guild_id, sender_id))
            receiver = copy.deepcopy(self._ensure_user(data, guild_id, receiver_id))
            resultado = _dar_moedas(sender, receiver, quantidade)
            if resultado["ok"]:
                data[gid][str(sender_id)] = normalizar_user_data(resultado["user_sender"])
                data[gid][str(receiver_id)] = normalizar_user_data(resultado["user_receiver"])
            return resultado
        return await self.store.update(mutator)

    async def trocar_ingredientes(
        self, guild_id: int, a_id: int, b_id: int,
        ing_a: str, qtd_a: int, ing_b: str, qtd_b: int,
    ) -> dict:
        def mutator(data: dict) -> dict:
            gid = str(guild_id)
            data.setdefault(gid, {})
            user_a = copy.deepcopy(self._ensure_user(data, guild_id, a_id))
            user_b = copy.deepcopy(self._ensure_user(data, guild_id, b_id))
            resultado = _executar_troca(user_a, user_b, ing_a, qtd_a, ing_b, qtd_b)
            if resultado["ok"]:
                data[gid][str(a_id)] = normalizar_user_data(resultado["user_a"])
                data[gid][str(b_id)] = normalizar_user_data(resultado["user_b"])
            return resultado
        return await self.store.update(mutator)
