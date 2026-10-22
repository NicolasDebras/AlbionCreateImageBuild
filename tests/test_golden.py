"""Rendu par défaut comparé au pixel près aux images de tests/golden/.

Elles ont été produites par le code d'origine (bot Lilium, avant l'extraction en lib) : le thème
lilas et les textes FR par défaut doivent les reproduire exactement.
Après un changement de rendu VOULU : `python tests/test_golden.py --update`, puis regarder les images.
"""
import io
import sys
from pathlib import Path

import pytest
from PIL import Image, ImageChops

from albion_create_image_build import item_ids, local_icon, render_build_image, render_compo_image, split_tier

GOLDEN = Path(__file__).parent / "golden"

BUILD = {
    "name": "Main Tank Avalon", "role": "TANK · Main tank", "type_acti": "PVE",
    "weapon": "Masse lourde 8.1 minimum", "notes": "Swap cape si besoin.\nBouffe : ragoût.",
    "items": {
        "mainhand": ["T8_MAIN_MACE_HELL@1", "2H_HOLYSTAFF"], "offhand": ["OFF_SHIELD"],
        "head": ["*"], "armor": ["T7_ARMOR_PLATE_SET1@3"], "shoes": ["SHOES_PLATE_SET1", "SHOES_CLOTH_SET1", "INCONNU"],
        "cape": ["CAPEITEM_FW_CAERLEON"], "food": ["T8_MEAL_STEW@2"], "potion": ["T3_POTION_STONESKIN@1"],
    },
}
BUILD_SWAPS = {**BUILD, "name": "Avec swaps",
               "items": {**BUILD["items"], "swaps": ["T8_OFF_SHIELD@4", "POTION_HEAL", "INCONNU"]}}
ROWS = [
    ("Party 1", "TANK · Main tank", 1, BUILD_SWAPS),
    ("Party 1", "HEAL", 2, {"name": "Heal sacré", "items": {"mainhand": ["2H_HOLYSTAFF"], "food": ["MEAL_OMELETTE"]}}),
    ("Party 1", "DPS", 3, {"name": "Un nom de build beaucoup trop long pour tenir dans la carte",
                           "items": {"cape": ["*"]}}),
    ("Party 2", "SUPPORT", 1, {"name": "Support", "items": {}}),
    ("Party 2", "SCOUT", 1, {"name": "Scout", "items": {"mainhand": ["MAIN_MACE_HELL"]}}),
]


def _icons():
    ids = item_ids(BUILD_SWAPS["items"])
    for row in ROWS:
        ids += [i for i in item_ids(row[3]["items"]) if i not in ids]
    return {i: local_icon(split_tier(i)[0]) for i in ids}


def _renders() -> dict[str, bytes]:
    icons = _icons()
    return {
        "ref_build.png": render_build_image(BUILD, icons, signature="Lilium · Bot"),
        "ref_build_swaps.png": render_build_image(BUILD_SWAPS, icons),
        "ref_compo.png": render_compo_image(ROWS, icons, signature="Lilium · Bot"),
    }


@pytest.mark.parametrize("name", ["ref_build.png", "ref_build_swaps.png", "ref_compo.png"])
def test_default_rendering_matches_golden_image(name):
    got = Image.open(io.BytesIO(_renders()[name])).convert("RGB")
    want = Image.open(GOLDEN / name).convert("RGB")
    assert got.size == want.size
    assert ImageChops.difference(got, want).getbbox() is None, f"{name} : rendu différent de l'image de référence"


def test_golden_fixture_uses_real_and_missing_icons():
    """Le cas de référence couvre bien icône trouvée ET icône manquante (« ? »)."""
    icons = _icons()
    assert icons["INCONNU"] is None
    assert sum(v is not None for v in icons.values()) >= 10


if __name__ == "__main__" and "--update" in sys.argv:
    for filename, png in _renders().items():
        (GOLDEN / filename).write_bytes(png)
        print("écrit", GOLDEN / filename)
