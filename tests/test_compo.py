"""render_compo_image, ordre des rôles, couleurs, pictogrammes."""
from helpers import colors, open_png, png

from albion_create_image_build import (
    COMPO_MAX_ROWS,
    COMPO_WIDTH,
    DEFAULT_THEME,
    CompoRow,
    fit_text,
    font,
    render_compo_image,
    role_color,
    role_icon,
    role_rank,
    sort_rows,
)
from albion_create_image_build._draw import SIGNATURE_H


def _rows(n_pf2=0):
    build = {"name": "Tank Masse", "items": {"mainhand": ["A", "B"], "cape": ["*"]}}
    rows = [("Party 1", "TANK", 2, build), ("Party 1", "HEAL", 1, {"name": "Heal", "items": {}})]
    return rows + [("Party 2", "DPS", 3, build)] * n_pf2


def test_size_and_gradient_background():
    img = open_png(render_compo_image(_rows(), {"A": png(), "B": None}))
    assert img.format == "PNG"
    assert img.width == COMPO_WIDTH
    assert img.convert("RGB").getpixel((2, 2)) == DEFAULT_THEME.accent              # haut du dégradé
    assert img.convert("RGB").getpixel((2, img.height - 1)) == DEFAULT_THEME.accent_dark


def test_accepts_compo_rows_and_tuples_alike():
    rows = [CompoRow("Party 1", "TANK", 1, {"name": "T", "items": {}})]
    assert render_compo_image(rows, {}) == render_compo_image([tuple(rows[0])], {})


def test_draws_alternative_choices_as_mini_icons():
    build = {"name": "B", "items": {"mainhand": ["MAIN", "ALT"]}}
    data = render_compo_image([("Party 1", "DPS", 1, build)], {"MAIN": png((255, 0, 0)), "ALT": png((0, 0, 255))})
    assert {(0, 0, 255), (255, 0, 0)} <= colors(data)


def test_missing_mini_icon_and_tier_badge():
    green = DEFAULT_THEME.enchant_colors[1]
    rows = [("Party 1", "TANK", 1, {"name": "T", "items": {"head": ["T8_HEAD_X@1", "NONE"]}})]
    assert green in colors(render_compo_image(rows, {"T8_HEAD_X@1": png((0, 0, 255))}), 1)


def test_with_twenty_builds_stays_light():
    build = {"name": "Build avec un nom beaucoup trop long pour la carte", "items": {"mainhand": ["A", "B", "C"]}}
    rows = [("Party 1" if i < 10 else "Party 2", f"ROLE{i}", 5, build) for i in range(20)]
    data = render_compo_image(rows, {"A": png(), "B": png(), "C": None})
    assert open_png(data).width == COMPO_WIDTH
    assert open_png(data).height > 20 * 76
    assert len(data) < 8 * 1024 * 1024   # sous la limite d'envoi Discord


def test_grows_with_rows_and_second_party():
    assert open_png(render_compo_image(_rows(n_pf2=1), {})).height > open_png(render_compo_image(_rows(), {})).height


def test_height_is_capped():
    """Une compo géante (5 000 lignes) ne doit pas produire une image de plusieurs Go."""
    capped = open_png(render_compo_image(_rows(n_pf2=COMPO_MAX_ROWS), {}))
    huge = open_png(render_compo_image(_rows(n_pf2=5000), {}))
    assert huge.height == capped.height


def test_widens_for_swaps():
    with_swaps = {"name": "B", "items": {"mainhand": ["A"], "swaps": ["X", "Y"]}}
    wide = open_png(render_compo_image([("Party 1", "TANK", 1, with_swaps)], {}))
    assert wide.width > open_png(render_compo_image(_rows(), {})).width == COMPO_WIDTH


def test_signature_band():
    rows = [("Party 1", "TANK", 1, {"name": "Tank", "items": {}})]
    plain = open_png(render_compo_image(rows, {}))
    assert open_png(render_compo_image(rows, {}, signature="Lilium · Bot")).height == plain.height + SIGNATURE_H


# ── Rôles ────────────────────────────────────────────────────────────────────

def test_base_role_rank_and_color():
    assert DEFAULT_THEME.base_role("TANK · Def tank") == "TANK"
    assert DEFAULT_THEME.base_role("SUPPORT 2") == "SUPPORT"
    assert DEFAULT_THEME.base_role("CALLER 2") == "CALLER 2"     # numéro gardé : rôle inconnu
    assert role_rank("TANK · Main tank") == role_rank("TANK") < role_rank("HEAL · X") < role_rank("SUPPORT") \
        < role_rank("DPS 2") < role_rank("CALLER")
    assert role_color("DPS") == role_color("DPS · Arcane") == DEFAULT_THEME.role_colors["DPS"]
    assert len({role_color(r) for r in ("TANK", "HEAL", "DPS", "SUPPORT")}) == 4
    assert role_color("CALLER") == DEFAULT_THEME.role_other_color


def test_sort_rows_by_party_then_role_stable():
    rows = [("P1", "DPS", 1, {}), ("P1", "SCOUT", 1, {}), ("P1", "TANK", 1, {}), ("P2", "HEAL", 1, {}),
            ("P1", "HEAL", 1, {}), ("P2", "TANK", 1, {}), ("P1", "DPS · 2", 1, {})]
    assert [(r.party, r.role) for r in sort_rows(rows)] == [
        ("P1", "TANK"), ("P1", "HEAL"), ("P1", "DPS"), ("P1", "DPS · 2"), ("P1", "SCOUT"),
        ("P2", "TANK"), ("P2", "HEAL"),
    ]


def test_role_icons_are_distinct_white_pictograms():
    shapes = ("swords", "shield", "cross", "star", "dot")
    images = [role_icon(s, 32) for s in shapes]
    assert all(i.size == (32, 32) and i.mode == "RGBA" for i in images)
    assert len({i.tobytes() for i in images}) == len(shapes)
    assert role_icon("inconnu", 32).tobytes() == role_icon("dot", 32).tobytes()


def test_fit_text_cuts_between_words_with_ellipsis():
    f = font(16)
    assert fit_text("Tank", f, 200) == "Tank"
    long = "Tank build numéro onze avec un nom vraiment très long"
    cut = fit_text(long, f, 200)
    assert cut.endswith("…") and f.getlength(cut) <= 200
    assert not cut[:-1].endswith(" ") and long.startswith(cut[:-1])
    one_word = fit_text("Supercalifragilisticexpialidocious" * 3, f, 120)
    assert one_word.endswith("…") and f.getlength(one_word) <= 120
