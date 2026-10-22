"""Image d'un build : disposition de l'inventaire du jeu (grille 3×3), objets de rechange à droite.

Fonction pure : elle reçoit les icônes déjà téléchargées (voir ``icons.IconFetcher``), donc
elle se teste sans réseau. Pour tout faire d'un coup en async : ``aio.build_image``.
"""
import textwrap
from collections.abc import Mapping
from typing import TypedDict

from PIL import Image, ImageDraw

from ._draw import MARGIN, SIGNATURE_H, centered_text, open_icon, tier_badge, to_png
from ._draw import signature as draw_signature
from .items import FREE_CHOICE, LAYOUT, SWAPS_KEY, SWAPS_MAX, ItemsInput, normalize_items
from .labels import Labels
from .text import fit_text, font
from .theme import DEFAULT_THEME, Theme


class Build(TypedDict, total=False):
    name: str           # titre
    role: str           # sous-titre, avec type_acti : « HEAL · PVP »
    type_acti: str
    weapon: str         # texte libre sous la grille
    notes: str          # idem, après weapon
    items: ItemsInput   # équipement (voir items.py)


CELL, LABEL_H, GAP, HEADER_H = 128, 22, 14, 96
WIDTH = MARGIN * 2 + CELL * 3 + GAP * 2     # largeur sans swaps
SWAP_CELL = 64
SWAP_GAP = 8
FOOTER_MAX_LINES = 8


def _draw_cell(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, slot: str, choices: list[str],
               icons: Mapping[str, bytes | None], theme: Theme, labels: Labels) -> None:
    filled = bool(choices)
    draw.rounded_rectangle((x, y, x + CELL, y + CELL), radius=14, fill=theme.surface,
                           outline=theme.accent if filled else theme.border, width=2 if filled else 1)
    centered_text(draw, (x, y + CELL + 2, x + CELL, y + CELL + LABEL_H), labels.slots.get(slot, slot),
                  font(14), theme.muted)
    if not filled:
        return
    if choices == [FREE_CHOICE]:
        centered_text(draw, (x, y, x + CELL, y + CELL), labels.free_choice, font(20, "SemiBold"), theme.accent)
        return

    n = len(choices)
    size = {1: 112, 2: 58, 3: 40}.get(n, 40)
    total_w = size * n + 4 * (n - 1)
    start_x = x + (CELL - total_w) // 2
    top = y + (CELL - size) // 2
    for i, item_id in enumerate(choices[:3]):
        ix = start_x + i * (size + 4)
        icon = open_icon(icons.get(item_id), size)
        if icon:
            img.paste(icon, (ix, top), icon)
        else:
            centered_text(draw, (ix, top, ix + size, top + size), "?", font(size // 2), theme.accent)
        tier_badge(draw, ix + 2, top + size - 2, item_id, theme, 14 if n == 1 else 11)
    if n > 1:
        centered_text(draw, (x, y + CELL - 22, x + CELL, y + CELL - 4), labels.n_choices.format(n=n),
                      font(13, "SemiBold"), theme.accent)


def _draw_swaps_column(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, top: int, swaps: list[str],
                       icons: Mapping[str, bytes | None], theme: Theme, labels: Labels) -> None:
    """Colonne « Swaps » à droite de la grille : une petite case par objet de rechange."""
    draw.text((x, top - 26), labels.swaps, font=font(14, "SemiBold"), fill=theme.muted)
    for i, item_id in enumerate(swaps):
        y = top + i * (SWAP_CELL + SWAP_GAP)
        draw.rounded_rectangle((x, y, x + SWAP_CELL, y + SWAP_CELL), radius=10, fill=theme.surface,
                               outline=theme.accent, width=2)
        icon = open_icon(icons.get(item_id), SWAP_CELL - 8)
        if icon:
            img.paste(icon, (x + 4, y + 4), icon)
        else:
            centered_text(draw, (x, y, x + SWAP_CELL, y + SWAP_CELL), "?", font(24), theme.accent)
        tier_badge(draw, x + 3, y + SWAP_CELL - 3, item_id, theme, 11)


def _footer_lines(build: Mapping) -> list[str]:
    lines: list[str] = []
    for block in (build.get("weapon", ""), build.get("notes", "")):
        if not (block and block.strip()):
            continue
        for para in block.strip().splitlines():
            lines.extend(textwrap.wrap(para, width=52) or [""])
    return lines[:FOOTER_MAX_LINES]


def render_build_image(build: Build | Mapping, icons: Mapping[str, bytes | None], *, signature: str = "",
                       theme: Theme = DEFAULT_THEME, labels: Labels = Labels.FR) -> bytes:
    """PNG du build : titre, rôle, grille façon inventaire (+ colonne Swaps à droite si besoin),
    texte libre en bas, puis `signature` en petit si elle est donnée.

    `icons` : {id d'objet: PNG ou None} ; une icône absente ou illisible est dessinée « ? ».
    """
    items = normalize_items(build.get("items"))
    swaps = [s for s in items.pop(SWAPS_KEY, []) if s != FREE_CHOICE][:SWAPS_MAX]
    footer_lines = _footer_lines(build)

    grid_h = 3 * (CELL + LABEL_H) + 2 * GAP
    footer_h = (len(footer_lines) * 22 + 24) if footer_lines else 0
    height = HEADER_H + grid_h + footer_h + MARGIN + (SIGNATURE_H if signature else 0)
    width = WIDTH + (SWAP_CELL + GAP) if swaps else WIDTH

    img = Image.new("RGBA", (width, height), theme.background)
    draw = ImageDraw.Draw(img)
    title_font = font(30, "Bold")
    draw.text((MARGIN, 22), fit_text(build.get("name") or labels.untitled, title_font, width - 2 * MARGIN),
              font=title_font, fill=theme.accent)
    subtitle = " · ".join(t for t in (build.get("role", ""), build.get("type_acti", "")) if t)
    draw.text((MARGIN, 60), subtitle, font=font(18), fill=theme.muted)

    for r, row in enumerate(LAYOUT):
        for c, slot in enumerate(row):
            if slot is None:
                continue
            x = MARGIN + c * (CELL + GAP)
            y = HEADER_H + r * (CELL + LABEL_H + GAP)
            _draw_cell(img, draw, x, y, slot, items.get(slot, []), icons, theme, labels)

    if swaps:
        _draw_swaps_column(img, draw, WIDTH - MARGIN + GAP, HEADER_H + 22, swaps, icons, theme, labels)

    y = HEADER_H + grid_h + 16
    for line in footer_lines:
        draw.text((MARGIN, y), line, font=font(16), fill=theme.text)
        y += 22
    if signature:
        draw_signature(draw, width, height, signature, theme.muted)
    return to_png(img)
