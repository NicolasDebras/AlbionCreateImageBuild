"""render_build_image : fonction pure, icônes fournies par le test."""
from helpers import colors, open_png, png

from albion_create_image_build import DEFAULT_THEME, SWAPS_MAX, WIDTH, item_ids, render_build_image, signature_text
from albion_create_image_build._draw import SIGNATURE_H
from albion_create_image_build.build import SWAP_CELL

BUILD = {
    "name": "Heal Sacré", "role": "HEAL", "type_acti": "PVP",
    "items": {"mainhand": ["2H_HOLYSTAFF", "2H_HOLYSTAFF_HELL"], "head": ["HEAD_CLOTH_SET2"],
              "cape": ["*"], "food": ["MEAL_STEW"]},
    "weapon": "", "notes": "",
}


def test_produces_png_with_expected_width():
    img = open_png(render_build_image(BUILD, {i: png() for i in item_ids(BUILD["items"])}))
    assert img.format == "PNG"
    assert img.width == WIDTH


def test_grows_with_notes_and_caps_footer():
    icons = {i: png() for i in item_ids(BUILD["items"])}
    short = open_png(render_build_image(BUILD, icons))
    long = open_png(render_build_image({**BUILD, "notes": "Ligne\n" * 5, "weapon": "Tier 8"}, icons))
    huge = open_png(render_build_image({**BUILD, "notes": "Ligne\n" * 50}, icons))
    capped = open_png(render_build_image({**BUILD, "notes": "Ligne\n" * 8}, icons))
    assert long.height > short.height
    assert huge.height == capped.height   # 8 lignes max


def test_tolerates_missing_or_broken_icons_and_empty_build():
    icons = {"2H_HOLYSTAFF": None, "HEAD_CLOTH_SET2": b"pas une image"}
    assert open_png(render_build_image(BUILD, icons)).width == WIDTH
    assert open_png(render_build_image({"name": "Vide", "items": {}}, {})).width == WIDTH
    assert open_png(render_build_image({}, {})).width == WIDTH      # ni nom ni objets
    assert open_png(render_build_image({"items": '{"head": ["H"]}', "notes": None}, {})).width == WIDTH


def test_draws_icon_pixels():
    """L'icône (rouge) doit apparaître dans l'image finale."""
    data = render_build_image({"name": "X", "items": {"armor": ["ARMOR_X"]}}, {"ARMOR_X": png((255, 0, 0))})
    assert (255, 0, 0) in colors(data, 4)


def test_draws_up_to_three_choices_per_slot():
    build = {"name": "X", "items": {"armor": ["R", "G", "B"]}}
    data = render_build_image(build, {"R": png((255, 0, 0)), "G": png((0, 255, 0)), "B": png((0, 0, 255))})
    assert {(255, 0, 0), (0, 255, 0), (0, 0, 255)} <= colors(data, 1)


def test_draws_tier_badge_with_enchant_color():
    """« T8_ARMOR_X@1 » : pastille 8.1 bordée de la couleur de l'enchantement .1 ; rien pour un tier libre."""
    green = DEFAULT_THEME.enchant_colors[1]
    icon = png((0, 0, 255))
    tiered = render_build_image({"name": "X", "items": {"armor": ["T8_ARMOR_X@1"], "swaps": ["T7_CAPE_X@1"]}},
                                {"T8_ARMOR_X@1": icon, "T7_CAPE_X@1": icon})
    plain = render_build_image({"name": "X", "items": {"armor": ["ARMOR_X"]}}, {"ARMOR_X": icon})
    assert green in colors(tiered, 1)
    assert green not in colors(plain, 1)


def test_swaps_widen_the_image_on_the_right():
    build = {**BUILD, "items": {**BUILD["items"], "swaps": [f"S{i}" for i in range(SWAPS_MAX + 2)]}}
    assert "S0" in item_ids(build["items"])
    img = open_png(render_build_image(build, {}))
    plain = open_png(render_build_image(BUILD, {}))
    assert img.width - plain.width == SWAP_CELL + 14
    assert img.height == plain.height


def test_free_choice_swap_is_ignored():
    build = {**BUILD, "items": {**BUILD["items"], "swaps": ["*"]}}
    assert open_png(render_build_image(build, {})).width == WIDTH


def test_signature_text_joins_non_empty_parts():
    assert signature_text("Lilium", "LiliumBot") == "Lilium · LiliumBot"
    assert signature_text("  ", "LiliumBot", None) == "LiliumBot"
    assert signature_text() == ""


def test_signature_adds_a_small_band_at_the_bottom():
    build = {"name": "Heal", "role": "HEAL", "items": {}}
    plain = open_png(render_build_image(build, {}))
    signed = open_png(render_build_image(build, {}, signature="Lilium · LiliumBot"))
    assert signed.height == plain.height + SIGNATURE_H
    assert signed.width == plain.width
    band = signed.crop((0, signed.height - SIGNATURE_H, signed.width, signed.height)).convert("L")
    assert band.getextrema()[0] != band.getextrema()[1]   # quelque chose est écrit (le fond est uni sinon)
