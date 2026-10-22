"""Raccourcis async : télécharge les icônes puis dessine dans un thread (Pillow prend 50 à 250 ms,
qui bloqueraient sinon la boucle d'événements d'un bot ou d'un serveur web)."""
import asyncio
from collections.abc import Iterable, Mapping

from .build import Build, render_build_image
from .compo import COMPO_MAX_ROWS, CompoRow, render_compo_image
from .icons import IconFetcher, default_fetcher
from .items import item_ids
from .labels import Labels
from .theme import DEFAULT_THEME, Theme


async def build_image(build: Build | Mapping, *, signature: str = "", theme: Theme = DEFAULT_THEME,
                      labels: Labels = Labels.FR, fetcher: IconFetcher | None = None) -> bytes:
    """PNG du build (voir ``render_build_image``), icônes comprises."""
    icons = await (fetcher or default_fetcher()).fetch(item_ids(build.get("items")))
    return await asyncio.to_thread(render_build_image, build, icons, signature=signature, theme=theme, labels=labels)


async def compo_image(rows: Iterable[CompoRow | tuple], *, signature: str = "", theme: Theme = DEFAULT_THEME,
                      labels: Labels = Labels.FR, fetcher: IconFetcher | None = None) -> bytes | None:
    """PNG de la compo (voir ``render_compo_image``), ou None s'il n'y a aucune ligne.
    Chaque icône n'est téléchargée qu'une fois, même si plusieurs builds la partagent."""
    rows = [CompoRow(*r) for r in list(rows)[:COMPO_MAX_ROWS]]
    if not rows:
        return None
    ids: list[str] = []
    for row in rows:
        ids.extend(i for i in item_ids(row.build.get("items")) if i not in ids)
    icons = await (fetcher or default_fetcher()).fetch(ids)
    return await asyncio.to_thread(render_compo_image, rows, icons, signature=signature, theme=theme, labels=labels)
