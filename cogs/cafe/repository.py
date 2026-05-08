from __future__ import annotations

import copy
from collections.abc import Callable

from utils.paths import CAFE_DATA_PATH
from utils.storage import JsonStore

from .service import normalizar_user_data


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

    async def get_all_users(self, guild_id: int) -> dict[str, dict]:
        data = await self.store.read()
        guild = data.get(str(guild_id), {})
        return {
            user_id: normalizar_user_data(user_data)
            for user_id, user_data in guild.items()
            if isinstance(user_data, dict)
        }
