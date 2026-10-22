"""Police embarquée (Inter, licence OFL) et mise en forme du texte."""
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

ASSETS_DIR = Path(__file__).resolve().parent / "assets"
FONT_FILE = ASSETS_DIR / "fonts" / "Inter.ttf"   # la police par défaut de Pillow n'a pas les accents

Font = ImageFont.FreeTypeFont | ImageFont.ImageFont


@lru_cache(maxsize=32)
def font(size: int, weight: str = "Regular") -> Font:
    """Inter à la graisse demandée (Regular, SemiBold, Bold…) ; police de Pillow si Inter est illisible.

    Mise en page BASIC imposée : avec raqm (présent ou non selon la machine), le texte se décale de
    quelques pixels ; ainsi une même image est identique partout (Windows, Linux, Docker slim)."""
    try:
        f = ImageFont.truetype(str(FONT_FILE), size, layout_engine=ImageFont.Layout.BASIC)
        f.set_variation_by_name(weight)
        return f
    except (OSError, ValueError):
        return ImageFont.load_default(size=size)


def fit_text(text: str, font: Font, max_width: float) -> str:
    """Raccourcit le texte (avec « … ») pour qu'il tienne en `max_width` pixels,
    en coupant de préférence entre deux mots."""
    if font.getlength(text) <= max_width:
        return text
    words = text.split()
    while len(words) > 1:
        words.pop()
        candidate = " ".join(words) + "…"
        if font.getlength(candidate) <= max_width:
            return candidate
    while text and font.getlength(text + "…") > max_width:   # un seul mot trop long
        text = text[:-1]
    return text + "…"


def signature_text(*parts: str) -> str:
    """« Lilium · LiliumBot » : morceaux non vides joints par « · » ('' si aucun)."""
    return " · ".join(t.strip() for t in parts if t and t.strip())
