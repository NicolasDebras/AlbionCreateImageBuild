"""Primitives de dessin communes aux images de build et de compo (privé)."""
import io
from collections.abc import Mapping

from PIL import Image, ImageDraw

from .items import split_tier
from .text import fit_text, font
from .theme import RGB, Theme

MARGIN = 28
SIGNATURE_H = 26   # bande du bas pour la signature (« Serveur · Bot »)


class IconImages:
    """Icônes d'un rendu, décodées une seule fois par id et redimensionnées une fois par taille
    (une compo répète souvent les mêmes objets d'une ligne à l'autre). Vit le temps d'un rendu."""

    def __init__(self, icons: Mapping[str, bytes | None]) -> None:
        self.icons = icons
        self._decoded: dict[str, Image.Image | None] = {}
        self._sized: dict[tuple[str, int], Image.Image | None] = {}

    def _decode(self, item_id: str) -> Image.Image | None:
        if item_id not in self._decoded:
            data = self.icons.get(item_id)
            try:
                self._decoded[item_id] = Image.open(io.BytesIO(data)).convert("RGBA") if data else None
            except Exception:
                self._decoded[item_id] = None
        return self._decoded[item_id]

    def get(self, item_id: str, size: int) -> Image.Image | None:
        """Icône de `item_id` en `size` px (redimensionnée en LANCZOS), ou None si absente/illisible."""
        key = (item_id, size)
        if key not in self._sized:
            img = self._decode(item_id)
            self._sized[key] = img.resize((size, size), Image.LANCZOS) if img is not None else None
        return self._sized[key]


def centered_text(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], text: str, f, fill) -> None:
    x0, y0, x1, y1 = box
    w = draw.textlength(text, font=f)
    draw.text((x0 + (x1 - x0 - w) / 2, y0 + (y1 - y0 - f.size) / 2), text, font=f, fill=fill)


def tier_badge(draw: ImageDraw.ImageDraw, x: int, bottom: int, item_id: str, theme: Theme, size: int = 13) -> None:
    """Pastille « 8.1 » posée au coin bas-gauche d'une icône (x, bottom) ; rien si le tier est libre."""
    _, tier, enchant = split_tier(item_id)
    if tier is None:
        return
    text, f = f"{tier}.{enchant}", font(size, "Bold")
    pad, h = 4, size + 6
    w = draw.textlength(text, font=f) + 2 * pad
    draw.rounded_rectangle((x, bottom - h, x + w, bottom), radius=h // 2, fill=theme.background,
                           outline=theme.enchant_colors.get(enchant, theme.muted), width=2)
    draw.text((x + pad, bottom - h + (h - size) / 2 - 1), text, font=f, fill=theme.text)


def signature(draw: ImageDraw.ImageDraw, width: int, height: int, text: str, fill: RGB) -> None:
    """Signature en petit, alignée à droite dans la bande du bas."""
    f = font(12)
    text = fit_text(text, f, width - 2 * MARGIN)
    w = draw.textlength(text, font=f)
    draw.text((width - MARGIN - w, height - SIGNATURE_H + 4), text, font=f, fill=fill)


def to_png(img: Image.Image) -> bytes:
    out = io.BytesIO()
    img.convert("RGB").save(out, format="PNG")
    return out.getvalue()
