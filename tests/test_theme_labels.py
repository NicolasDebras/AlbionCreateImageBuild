"""Thème et textes personnalisés : la lib n'est pas figée sur Lilium (lilas, français)."""
import dataclasses

import pytest
from helpers import colors, open_png, png

from albion_create_image_build import DEFAULT_THEME, Labels, Theme, render_build_image, render_compo_image

BUILD = {"name": "X", "role": "TANK", "items": {"head": ["*"], "armor": ["A", "B"], "swaps": ["S"]}}
ROWS = [("Party 1", "SCOUT", 1, {"name": "Scout", "items": {"cape": ["*"]}})]


def test_theme_is_immutable_and_has_lilium_defaults():
    assert DEFAULT_THEME.accent == (200, 162, 255)
    with pytest.raises(dataclasses.FrozenInstanceError):
        DEFAULT_THEME.accent = (0, 0, 0)
    with pytest.raises(TypeError):
        DEFAULT_THEME.role_colors["TANK"] = (0, 0, 0)


def test_custom_background_and_accent_are_used():
    theme = Theme(background=(1, 2, 3), accent=(250, 10, 10))
    data = render_build_image(BUILD, {}, theme=theme)
    assert open_png(data).convert("RGB").getpixel((0, 0)) == (1, 2, 3)
    assert (250, 10, 10) in colors(data, 1)
    assert DEFAULT_THEME.accent not in colors(data, 1)


def test_custom_role_color_and_order():
    gold = (240, 200, 0)
    theme = Theme(role_order=("SCOUT", "TANK"), role_colors={"SCOUT": gold}, role_shapes={"SCOUT": "star"})
    assert theme.role_rank("SCOUT") == 0 and theme.role_rank("HEAL") == 2
    assert theme.base_role("SCOUT 2") == "SCOUT"
    assert gold in colors(render_compo_image(ROWS, {}, theme=theme), 1)
    assert gold not in colors(render_compo_image(ROWS, {}), 1)


def test_custom_role_shape_changes_the_badge():
    star = Theme(role_shapes={"SCOUT": "star"})
    assert render_compo_image(ROWS, {}, theme=star) != render_compo_image(ROWS, {})


def test_english_labels_change_the_drawing_not_the_size():
    fr, en = render_build_image(BUILD, {}), render_build_image(BUILD, {}, labels=Labels.EN)
    assert fr != en
    assert open_png(fr).size == open_png(en).size
    assert render_compo_image(ROWS, {}, labels=Labels.EN) != render_compo_image(ROWS, {})


def test_labels_are_complete_and_customisable():
    for labels in (Labels.FR, Labels.EN):
        assert set(labels.slots) == {"mainhand", "offhand", "head", "armor", "shoes", "cape", "food", "potion"}
        assert labels.n_choices.format(n=2) and labels.compo_header.format(players=5, builds=2)
    custom = dataclasses.replace(Labels.EN, free_choice="Any")
    assert render_build_image(BUILD, {}, labels=custom) != render_build_image(BUILD, {}, labels=Labels.EN)


def test_unknown_slot_label_falls_back_to_slot_key():
    labels = dataclasses.replace(Labels.FR, slots={})
    assert open_png(render_build_image(BUILD, {"A": png()}, labels=labels)).format == "PNG"
