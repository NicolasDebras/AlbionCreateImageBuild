"""Icônes des objets : d'abord celles embarquées dans le paquet (assets/icons/<ID>.png),
sinon le CDN officiel d'Albion (render.albiononline.com).

``IconFetcher`` garde son propre cache et ses réglages ; ``default_fetcher()`` en partage un
pour tout le processus. Ne lève jamais d'erreur réseau : une icône introuvable, en échec ou
hors délai vaut ``None`` (dessinée « ? »).
"""
import asyncio
import re
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

import aiohttp

from .items import SPELL_PREFIX, split_tier
from .text import ASSETS_DIR

ICONS_DIR = ASSETS_DIR / "icons"
ICON_URL_TIER = "https://render.albiononline.com/v1/item/T{tier}_{item_id}.png?size=128"
ICON_URL_EXACT = "https://render.albiononline.com/v1/item/{item_id}.png?size=128"
SPELL_ICON_URL = "https://render.albiononline.com/v1/spell/{spell_id}.png?size=128"
_ITEM_ID_RE = re.compile(r"^[A-Z0-9_@]{1,80}$")   # format des ids Albion (ex. 2H_HOLYSTAFF_HELL@2)

Icons = dict[str, bytes | None]


def local_icon(item_id: str, icons_dir: Path = ICONS_DIR) -> bytes | None:
    """Icône embarquée de l'objet (id sans tier), ou None (id absent ou suspect)."""
    if not item_id or "/" in item_id or "\\" in item_id or ".." in item_id:
        return None
    try:
        return (icons_dir / f"{item_id}.png").read_bytes()
    except OSError:
        return None


class IconFetcher:
    """Télécharge des icônes en parallèle, avec cache borné.

    - id avec tier (« T7_MAIN_SWORD@2 ») : icône exacte du CDN (chiffre du tier, lueur
      d'enchantement), sinon celle de l'objet de base ;
    - objet de base : icône embarquée, sinon CDN du tier 8 au tier 1 (la bouffe et les potions
      n'existent pas à tous les tiers) ;
    - sort (« spell:SPRINTHOT ») : icône du sort sur le CDN.

    Seules les réponses sûres (200, 404) sont mises en cache : une lenteur passagère du CDN
    ne marque pas l'icône comme absente.
    """

    def __init__(self, *, icons_dir: Path | None = ICONS_DIR, request_timeout: float = 8, retries: int = 2,
                 concurrency: int = 6, deadline: float = 40, cache_max: int = 2000,
                 max_bytes: int = 2 * 1024 * 1024,
                 session_factory: Callable[[], Any] = aiohttp.ClientSession) -> None:
        self.icons_dir = icons_dir          # None : pas d'icônes locales, tout vient du CDN
        self.request_timeout = request_timeout
        self.retries = retries
        self.concurrency = concurrency
        self.deadline = deadline            # budget total d'un fetch()
        self.cache_max = cache_max
        self.max_bytes = max_bytes          # une icône 128 px fait ~20 Ko : au-delà, réponse ignorée
        self.session_factory = session_factory
        self.cache: Icons = {}

    def local(self, item_id: str) -> bytes | None:
        return local_icon(item_id, self.icons_dir) if self.icons_dir is not None else None

    async def _get(self, session, url: str) -> tuple[bool, bytes | None]:
        """(réponse sûre, contenu) ; (False, None) après les tentatives (lenteur, réseau, 5xx)."""
        for _ in range(self.retries):
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=self.request_timeout)) as resp:
                    if resp.status == 200:
                        # read(n) rend ce qui est déjà arrivé : lire jusqu'au bout, abandon au-delà de max_bytes
                        chunks, size = [], 0
                        while chunk := await resp.content.read(64 * 1024):
                            size += len(chunk)
                            if size > self.max_bytes:
                                return True, None
                            chunks.append(chunk)
                        return True, b"".join(chunks)
                    if resp.status == 404:
                        return True, None
            except (TimeoutError, aiohttp.ClientError):
                pass
        return False, None

    def _remember(self, item_id: str, data: bytes | None) -> bytes | None:
        self.cache[item_id] = data
        return data

    async def fetch_one(self, session, item_id: str) -> bytes | None:
        """Icône d'un objet (voir la classe), avec le cache."""
        if item_id in self.cache:
            return self.cache[item_id]
        spell = item_id[len(SPELL_PREFIX):] if (item_id or "").startswith(SPELL_PREFIX) else None
        if not _ITEM_ID_RE.match(item_id if spell is None else spell) or (spell and "@" in spell):
            return None
        if len(self.cache) >= self.cache_max:
            self.cache.clear()
        if spell is not None:
            sure, data = await self._get(session, SPELL_ICON_URL.format(spell_id=spell))
            return self._remember(item_id, data) if sure else None
        base, tier, _ = split_tier(item_id)
        if tier is not None:
            sure, data = await self._get(session, ICON_URL_EXACT.format(item_id=item_id))
            if not sure:
                return None
            if data is not None:
                return self._remember(item_id, data)
        local = self.local(base)
        if local is not None:
            return self._remember(item_id, local)
        for t in range(8, 0, -1):
            sure, data = await self._get(session, ICON_URL_TIER.format(tier=t, item_id=base))
            if not sure:
                return None
            if data is not None:
                return self._remember(item_id, data)
        return self._remember(item_id, None)

    async def fetch(self, ids: Iterable[str]) -> Icons:
        """{id: icône ou None} pour chaque id (doublons ignorés), au plus `concurrency` requêtes
        à la fois et `deadline` secondes en tout."""
        ids = list(dict.fromkeys(ids))
        if not ids:
            return {}
        sem = asyncio.Semaphore(self.concurrency)

        async def one(session, item_id):
            async with sem:
                return await self.fetch_one(session, item_id)

        async with self.session_factory() as session:
            tasks = {asyncio.ensure_future(one(session, i)): i for i in ids}
            done, pending = await asyncio.wait(tasks, timeout=self.deadline)
            for t in pending:
                t.cancel()
            await asyncio.gather(*pending, return_exceptions=True)
        icons: Icons = dict.fromkeys(ids)
        for t in done:
            if not t.cancelled() and t.exception() is None:
                icons[tasks[t]] = t.result()
        return icons


_default: IconFetcher | None = None


def default_fetcher() -> IconFetcher:
    """IconFetcher partagé par tout le processus (créé au premier appel)."""
    global _default
    if _default is None:
        _default = IconFetcher()
    return _default
