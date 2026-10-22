from albion_create_image_build import has_tiered_gear, item_ids, normalize_items, split_tier


def test_split_tier():
    assert split_tier("T8_MAIN_SWORD@1") == ("MAIN_SWORD", 8, 1)
    assert split_tier("T7_2H_HOLYSTAFF") == ("2H_HOLYSTAFF", 7, 0)
    assert split_tier("MAIN_SWORD") == ("MAIN_SWORD", None, 0)
    assert split_tier("T9_MAIN_SWORD") == ("T9_MAIN_SWORD", None, 0)    # tier hors 1–8 : id nu
    assert split_tier("T8_MAIN_SWORD@5") == ("T8_MAIN_SWORD@5", None, 0)
    assert split_tier("") == ("", None, 0)


def test_normalize_items_accepts_old_format_and_json_string():
    assert normalize_items({"mainhand": "MAIN_SWORD", "head": [], "cape": ["*"], "food": None}) == {
        "mainhand": ["MAIN_SWORD"], "cape": ["*"],
    }
    assert normalize_items('{"head": ["HEAD_PLATE_SET1"]}') == {"head": ["HEAD_PLATE_SET1"]}
    assert normalize_items("") == {}
    assert normalize_items(None) == {}
    assert normalize_items({"mainhand": ["", "A"]}) == {"mainhand": ["A"]}


def test_item_ids_skips_free_choice_and_duplicates_in_order():
    items = {"mainhand": ["A", "B"], "offhand": ["A"], "cape": ["*"], "swaps": ["C"]}
    assert item_ids(items) == ["A", "B", "C"]
    assert item_ids(None) == []


def test_has_tiered_gear_ignores_consumables():
    assert has_tiered_gear({"mainhand": ["T8_MAIN_SWORD@1"]})
    assert has_tiered_gear({"swaps": ["T7_OFF_SHIELD"]})
    assert has_tiered_gear('{"head": ["T4_HEAD_CLOTH_SET1"]}')
    assert not has_tiered_gear({"mainhand": ["MAIN_SWORD"], "food": ["T8_MEAL_STEW@1"], "potion": ["T3_POTION_HEAL"]})
    assert not has_tiered_gear(None)
