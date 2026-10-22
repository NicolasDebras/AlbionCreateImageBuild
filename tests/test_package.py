"""Le paquet installé : API publique, version, assets embarqués (police, icônes)."""
from importlib.metadata import version

from PIL import Image, ImageFont

import albion_create_image_build as lib
from albion_create_image_build import ICONS_DIR, local_icon
from albion_create_image_build.text import FONT_FILE, font


def test_public_api_is_exported():
    for name in lib.__all__:
        assert hasattr(lib, name), name
    assert len(set(lib.__all__)) == len(lib.__all__)


def test_version_matches_package_metadata():
    assert lib.__version__ == version("albion-create-image-build")


def test_bundled_font_has_accents_and_weights():
    f = ImageFont.truetype(str(FONT_FILE), 16)
    assert f.getlength("Épée") > 0
    assert isinstance(font(16, "Bold"), ImageFont.FreeTypeFont)


def test_font_layout_is_the_same_on_every_machine():
    """raqm (Linux avec libfribidi) décalerait le texte : les images de référence ne tiendraient plus."""
    assert font(16).layout_engine == ImageFont.Layout.BASIC


def test_font_falls_back_to_pillow_default_on_unknown_weight():
    assert font(15, "Inexistante") is not None


def test_bundled_icons_are_real_pngs():
    assert len(list(ICONS_DIR.glob("*.png"))) > 200
    for item_id in ("MAIN_MACE_HELL", "MEAL_OMELETTE", "POTION_MOB_RESET"):
        data = local_icon(item_id)
        assert data and data.startswith(b"\x89PNG")
        with Image.open(ICONS_DIR / f"{item_id}.png") as img:
            assert img.format == "PNG"
    assert local_icon("../etc") is None
    assert local_icon("ABSENT_DU_PAQUET") is None
