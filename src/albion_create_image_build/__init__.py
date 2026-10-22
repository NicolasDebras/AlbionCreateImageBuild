"""Images PNG de builds et de compos Albion Online (disposition de l'inventaire du jeu, icônes officielles).

    from albion_create_image_build import build_image, render_build_image, Labels, Theme

    png = await build_image({"name": "Heal", "items": {"mainhand": ["T8_2H_HOLYSTAFF@1"]}})
    png = render_build_image(build, icons, theme=Theme(accent=(255, 80, 80)), labels=Labels.EN)
"""
from .aio import build_image, compo_image
from .build import WIDTH, Build, render_build_image
from .compo import COMPO_MAX_ROWS, COMPO_WIDTH, CompoRow, render_compo_image, role_icon, sort_rows
from .icons import ICONS_DIR, IconFetcher, default_fetcher, local_icon
from .items import (
    FREE_CHOICE,
    LAYOUT,
    SLOTS,
    SWAPS_KEY,
    SWAPS_MAX,
    TIER_FREE_SLOTS,
    has_tiered_gear,
    item_ids,
    normalize_items,
    split_tier,
)
from .labels import Labels
from .text import fit_text, font, signature_text
from .theme import DEFAULT_THEME, ROLE_SHAPES, Theme, role_color, role_rank

__version__ = "1.0.0"

__all__ = [
    "COMPO_MAX_ROWS", "COMPO_WIDTH", "DEFAULT_THEME", "FREE_CHOICE", "ICONS_DIR", "LAYOUT", "ROLE_SHAPES", "SLOTS",
    "SWAPS_KEY", "SWAPS_MAX", "TIER_FREE_SLOTS", "WIDTH",
    "Build", "CompoRow", "IconFetcher", "Labels", "Theme",
    "build_image", "compo_image", "default_fetcher", "fit_text", "font", "has_tiered_gear", "item_ids", "local_icon",
    "normalize_items", "render_build_image", "render_compo_image", "role_color", "role_icon", "role_rank",
    "signature_text", "sort_rows", "split_tier",
]
