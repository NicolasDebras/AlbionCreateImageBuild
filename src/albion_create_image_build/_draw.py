"""Primitives de dessin communes aux images de build et de compo (privé)."""
import io

from PIL import Image, ImageDraw

from .items import split_tier
from .text import fit_text, font
from .theme import RGB, Theme

MARGIN = 28
SIGNATURE_H = 26   # bande du bas pour la signature (« Serveur · Bot »)


def open_icon(data: bytes | None, size: int) -> Image.Image | None:
    if not data:
        return None
    try:
        return Image.open(io.BytesIO(data)).convert("RGBA").resize((size, size), Image.LANCZOS)
    except Exception:
        return None


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
