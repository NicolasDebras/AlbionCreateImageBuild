"""Télécharge les icônes Albion embarquées dans le paquet (outil de dev, pas utilisé à l'exécution).

Embarquer les icônes évite de dépendre du CDN d'Albion (lent / instable depuis certains
hébergeurs) ; le CDN reste un secours pour un objet absent.

Usage :
    python scripts/download_icons.py --catalog items.json                # [{"id": "X", "icon": "T8_X"}, ...]
    python scripts/download_icons.py --catalog items.json --force        # re-télécharge tout
    python scripts/download_icons.py --catalog items.json --out dossier  # ailleurs que dans le paquet

Par défaut, le catalogue est celui du site Lilium s'il est à côté (../lilium-site/api/app/data/items.json).
"""
import argparse
import asyncio
import io
import json
import sys
from pathlib import Path

import aiohttp
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
ICONS_DIR = ROOT / "src" / "albion_create_image_build" / "assets" / "icons"
DEFAULT_CATALOG = ROOT.parent / "lilium-site" / "api" / "app" / "data" / "items.json"
URL = "https://render.albiononline.com/v1/item/{icon}.png?size=128"


def compress(data: bytes) -> bytes:
    """PNG 128 px, palette 256 couleurs + alpha : ~4× plus léger, invisible à cette taille."""
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    out = io.BytesIO()
    img.quantize(colors=256, method=Image.Quantize.FASTOCTREE).save(out, format="PNG", optimize=True)
    return out.getvalue()


async def download(session, sem, item, out: Path, force: bool) -> str:
    target = out / f"{item['id']}.png"
    if target.exists() and not force:
        return "skip"
    async with sem:
        for _ in range(3):
            try:
                async with session.get(URL.format(icon=item["icon"]), timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status != 200:
                        return f"HTTP {resp.status}"
                    target.write_bytes(compress(await resp.read()))
                    return "ok"
            except (TimeoutError, aiohttp.ClientError):
                await asyncio.sleep(1)
    return "échec"


async def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="JSON [{id, icon}, ...]")
    parser.add_argument("--out", type=Path, default=ICONS_DIR, help="dossier de sortie")
    parser.add_argument("--force", action="store_true", help="re-télécharge les icônes déjà présentes")
    args = parser.parse_args(argv)

    items = json.loads(args.catalog.read_text(encoding="utf-8"))
    args.out.mkdir(parents=True, exist_ok=True)
    sem = asyncio.Semaphore(6)
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*(download(session, sem, it, args.out, args.force) for it in items))
    failed = [(it["id"], r) for it, r in zip(items, results, strict=True) if r not in ("ok", "skip")]
    print(f"{results.count('ok')} téléchargées, {results.count('skip')} déjà présentes, {len(failed)} en échec")
    for item_id, reason in failed:
        print(f"  ✗ {item_id} : {reason}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main(sys.argv[1:])))
