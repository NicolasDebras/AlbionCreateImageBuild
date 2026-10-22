"""Image d'une compo : une carte par build (rôle × nombre, nom, icônes des 8 cases + swaps),
regroupées par party, sur un fond en dégradé.

Fonction pure, comme ``build.render_build_image``. Pour tout faire d'un coup en async : ``aio.compo_image``.
"""
from collections.abc import Iterable, Mapping
from typing import NamedTuple

from PIL import Image, ImageDraw

from ._draw import MARGIN, SIGNATURE_H, centered_text, open_icon, tier_badge, to_png
from ._draw import signature as draw_signature
from .build import Build
from .items import FREE_CHOICE, SLOTS, SWAPS_KEY, SWAPS_MAX, normalize_items
from .labels import Labels
from .text import fit_text, font
from .theme import DEFAULT_THEME, RGB, Theme, mix


class CompoRow(NamedTuple):
    party: str      # « Party 1 » : les lignes sont regroupées par party, dans l'ordre d'apparition
    role: str       # « TANK », « TANK · Main tank », « SCOUT »…
    count: int      # nombre de joueurs sur ce build
    build: Build | Mapping


COMPO_SLOTS = SLOTS
C_ICON, C_ICON_GAP, C_ROW_H, C_LEFT = 52, 6, 76, 250
C_HEADER = 56    # hauteur de l'en-tête (« N joueurs · M builds »)
C_MINI = 22      # mini-icône d'un choix alternatif (coin bas-droit de la case)
COMPO_WIDTH = MARGIN * 2 + C_LEFT + len(COMPO_SLOTS) * (C_ICON + C_ICON_GAP)   # largeur sans swaps
COMPO_MAX_ROWS = 40   # la hauteur suit le nombre de lignes : au-delà, image démesurée


def role_icon(shape: str, size: int) -> Image.Image:
    """Pictogramme blanc (``theme.ROLE_SHAPES`` : swords, shield, cross, star ; pastille ronde sinon),
    dessiné en 64 px puis réduit pour des bords lissés."""
    c = 64
    img = Image.new("RGBA", (c, c), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    white = (255, 255, 255, 255)
    if shape == "swords":
        for flip in (False, True):
            fx = (lambda x: c - x) if flip else (lambda x: x)
            d.line((fx(16), 48, fx(58), 6), fill=white, width=7)    # lame
            d.line((fx(8), 38, fx(26), 56), fill=white, width=7)    # garde
            d.line((fx(4), 60, fx(16), 48), fill=white, width=8)    # poignée
    elif shape == "shield":
        d.polygon([(8, 8), (32, 2), (56, 8), (54, 34), (32, 62), (10, 34)], fill=white)
    elif shape == "cross":
        d.rounded_rectangle((24, 4, 40, 60), radius=4, fill=white)
        d.rounded_rectangle((4, 24, 60, 40), radius=4, fill=white)
    elif shape == "star":
        d.polygon([(32, 0), (41, 23), (64, 32), (41, 41), (32, 64), (23, 41), (0, 32), (23, 23)], fill=white)
    else:
        d.ellipse((16, 16, 48, 48), fill=white)
    return img.resize((size, size), Image.LANCZOS)


def _draw_role_badge(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, role: str, theme: Theme) -> int:
    """Pastille « [pictogramme] RÔLE » de la couleur du rôle ; renvoie l'abscisse de son bord droit."""
    base = theme.base_role(role)
    f = font(15, "Bold")
    label = fit_text(base, f, 130)
    h, icon_s = 28, 16
    w = 10 + icon_s + 6 + int(draw.textlength(label, font=f)) + 12
    draw.rounded_rectangle((x, y, x + w, y + h), radius=h // 2, fill=theme.role_color(role))
    icon = role_icon(theme.role_shape(role), icon_s)
    img.paste(icon, (x + 10, y + (h - icon_s) // 2), icon)
    draw.text((x + 10 + icon_s + 6, y + (h - 15) / 2 - 2), label, font=f, fill=(255, 255, 255))
    return x + w


def _gradient(width: int, height: int, top: RGB, bottom: RGB) -> Image.Image:
    img = Image.new("RGBA", (width, height))
    draw = ImageDraw.Draw(img)
    for y in range(height):
        draw.line([(0, y), (width, y)], fill=mix(top, bottom, y / max(height - 1, 1)))
    return img


def _draw_small_slot(img: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, choices: list[str],
                     icons: Mapping[str, bytes | None], theme: Theme, labels: Labels) -> None:
    draw.rounded_rectangle((x, y, x + C_ICON, y + C_ICON), radius=8, fill=theme.surface)
    if not choices:
        return
    if choices == [FREE_CHOICE]:
        mid = y + C_ICON // 2
        first, second = labels.free_choice_lines
        centered_text(draw, (x, mid - 15, x + C_ICON, mid), first, font(12, "Bold"), theme.accent)
        centered_text(draw, (x, mid - 1, x + C_ICON, mid + 14), second, font(12, "Bold"), theme.accent)
        return
    icon = open_icon(icons.get(choices[0]), C_ICON)
    if icon:
        img.paste(icon, (x, y), icon)
    else:
        centered_text(draw, (x, y, x + C_ICON, y + C_ICON), "?", font(24, "Bold"), theme.accent)
    # En haut à gauche (sur le chiffre du tier) : le bas est pris par les mini-icônes des autres choix
    tier_badge(draw, x + 1, y + 17, choices[0], theme, 10)
    # Autres choix possibles : mini-icônes cerclées dans le coin bas-droit
    by = y + C_ICON - C_MINI + 4
    for i, alt in enumerate(choices[1:]):
        bx = x + C_ICON - C_MINI + 4 - i * (C_MINI + 2)
        draw.rounded_rectangle((bx - 1, by - 1, bx + C_MINI + 1, by + C_MINI + 1), radius=6, fill=theme.surface,
                               outline=theme.accent, width=2)
        mini = open_icon(icons.get(alt), C_MINI)
        if mini:
            img.paste(mini, (bx, by), mini)
        else:
            centered_text(draw, (bx, by, bx + C_MINI, by + C_MINI), "?", font(12, "Bold"), theme.accent)


def _swaps(items: dict[str, list[str]]) -> list[str]:
    return [s for s in items.get(SWAPS_KEY, []) if s != FREE_CHOICE][:SWAPS_MAX]


def render_compo_image(rows: Iterable[CompoRow | tuple], icons: Mapping[str, bytes | None], *,
                       signature: str = "", theme: Theme = DEFAULT_THEME, labels: Labels = Labels.FR) -> bytes:
    """PNG de la compo. `rows` = [(party, rôle, nombre, build)] dans l'ordre d'affichage (voir
    ``sort_rows``), au plus COMPO_MAX_ROWS ; une couleur d'accent par rôle (``theme.role_colors``)."""
    rows = [CompoRow(*r) for r in list(rows)[:COMPO_MAX_ROWS]]
    items_of = [normalize_items(r.build.get("items")) for r in rows]
    max_swaps = max((len(_swaps(items)) for items in items_of), default=0)
    width = COMPO_WIDTH + (14 + max_swaps * (C_ICON + C_ICON_GAP) if max_swaps else 0)
    parties = list(dict.fromkeys(r.party for r in rows))
    multi_party = len(parties) > 1
    height = (C_HEADER + len(rows) * (C_ROW_H + 10) + (len(parties) * 34 if multi_party else 0) + MARGIN
              + (SIGNATURE_H if signature else 0))
    img = _gradient(width, height, theme.accent, theme.accent_dark)
    draw = ImageDraw.Draw(img)

    header = labels.compo_header.format(players=sum(r.count for r in rows), builds=len(rows))
    draw.text((MARGIN, 20), header, font=font(17, "Bold"), fill=theme.ink)

    y = C_HEADER
    for party in parties:
        if multi_party:
            draw.text((MARGIN, y), party.upper(), font=font(16, "Bold"), fill=theme.ink)
            y += 34
        for row, items in zip(rows, items_of, strict=True):
            if row.party != party:
                continue
            accent = theme.role_color(row.role)
            draw.rounded_rectangle((MARGIN, y, width - MARGIN, y + C_ROW_H), radius=14,
                                   fill=mix(theme.background, accent, .10), outline=mix(theme.background, accent, .55),
                                   width=2)
            draw.rounded_rectangle((MARGIN + 10, y + 12, MARGIN + 15, y + C_ROW_H - 12), radius=3, fill=accent)
            # Pastille du rôle et « ×N », puis le nom du build dans la couleur du rôle, coupé avec « … »
            right = _draw_role_badge(img, draw, MARGIN + 26, y + 10, row.role, theme)
            draw.text((right + 8, y + 12), f"×{row.count}", font=font(18, "Bold"), fill=theme.text)
            draw.text((MARGIN + 26, y + 46), fit_text(row.build.get("name") or "", font(16, "SemiBold"), C_LEFT - 38),
                      font=font(16, "SemiBold"), fill=accent)
            ix = MARGIN + C_LEFT
            for slot in COMPO_SLOTS:
                _draw_small_slot(img, draw, ix, y + (C_ROW_H - C_ICON) // 2, items.get(slot, []), icons, theme, labels)
                ix += C_ICON + C_ICON_GAP
            swaps = _swaps(items)
            if swaps:   # à droite des 8 cases, après un trait de la couleur du rôle
                draw.line((ix + 4, y + 14, ix + 4, y + C_ROW_H - 14), fill=accent, width=2)
                ix += 14
                for item_id in swaps:
                    _draw_small_slot(img, draw, ix, y + (C_ROW_H - C_ICON) // 2, [item_id], icons, theme, labels)
                    ix += C_ICON + C_ICON_GAP
            y += C_ROW_H + 10
    if signature:
        draw_signature(draw, width, height, signature, mix(theme.ink, theme.accent_dark, .25))
    return to_png(img)


def sort_rows(rows: Iterable[CompoRow | tuple], theme: Theme = DEFAULT_THEME) -> list[CompoRow]:
    """Lignes regroupées par party (ordre d'apparition) puis par rôle (``theme.role_order``), tri stable."""
    rows = [CompoRow(*r) for r in rows]
    parties = list(dict.fromkeys(r.party for r in rows))
    return sorted(rows, key=lambda r: (parties.index(r.party), theme.role_rank(r.role)))
