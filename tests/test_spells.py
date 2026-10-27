"""Sorts : lecture (items.py), rendu de la section et de la case Bottes, icônes « spell: »."""
import asyncio

from helpers import FakeSession, colors, open_png, png

from albion_create_image_build import (
    SHOES_ANY,
    SPELL_ICON_URL,
    WIDTH,
    IconFetcher,
    Labels,
    build_image,
    normalize_spells,
    render_build_image,
    shoes_any_spells,
    spell_ids,
    spell_rows,
)
from albion_create_image_build.build import SPELL_ROW_H, SPELL_ROWS_MAX

ITEMS = {"mainhand": ["T8_2H_LONGBOW@1", "2H_BOW"], "armor": ["ARMOR_PLATE_SET1"], "shoes": ["*"],
         "head": ["*"], "cape": ["CAPE"]}
SPELLS = {
    "2H_LONGBOW": {"p": "PASSIVE_SLOWPOISON", "q": "MULTISHOT2", "e": "ARROWRAIN"},
    "ARMOR_PLATE_SET1": {"a": "TAUNT", "p2": "PASSIVE_THREAT"},
    "CAPE": {"p": "IGNORE"},                     # cape : pas de sorts dessinés
    "HORS_BUILD": {"q": "X"},
    SHOES_ANY: {"a": "SPRINT_CD_REDUCTION", "p": "PASSIVE_BALANCE"},
}


def test_normalize_spells_orders_keys_and_drops_empty():
    raw = '{"A": {"p": "P1", "q": "Q1", "w": ""}, "B": {}, "C": "x"}'
    assert normalize_spells(raw) == {"A": {"q": "Q1", "p": "P1"}}
    assert normalize_spells(None) == {} and normalize_spells("") == {}


def test_spell_rows_follow_gear_order_and_base_ids():
    assert spell_rows(ITEMS, SPELLS) == [
        ("mainhand", "T8_2H_LONGBOW@1", {"q": "MULTISHOT2", "e": "ARROWRAIN", "p": "PASSIVE_SLOWPOISON"}),
        ("armor", "ARMOR_PLATE_SET1", {"a": "TAUNT", "p2": "PASSIVE_THREAT"}),
    ]


def test_shoes_any_only_without_specific_boots():
    assert shoes_any_spells(ITEMS, SPELLS) == {"a": "SPRINT_CD_REDUCTION", "p": "PASSIVE_BALANCE"}
    assert shoes_any_spells({}, SPELLS) == {"a": "SPRINT_CD_REDUCTION", "p": "PASSIVE_BALANCE"}
    assert shoes_any_spells({"shoes": ["SHOES_PLATE_SET1"]}, SPELLS) == {}


def test_spell_ids_without_duplicates():
    ids = spell_ids(ITEMS, {**SPELLS, "2H_BOW": {"q": "MULTISHOT2"}})
    assert ids == ["spell:MULTISHOT2", "spell:ARROWRAIN", "spell:PASSIVE_SLOWPOISON", "spell:TAUNT",
                   "spell:PASSIVE_THREAT", "spell:SPRINT_CD_REDUCTION", "spell:PASSIVE_BALANCE"]


def _icons(build):
    from albion_create_image_build import item_ids
    return {i: png((0, 200, 0)) for i in item_ids(build["items"]) + spell_ids(build["items"], build.get("spells"))}


def test_spells_section_grows_image():
    plain = {"name": "B", "items": ITEMS}
    with_spells = {**plain, "spells": {k: v for k, v in SPELLS.items() if k != SHOES_ANY}}
    a = open_png(render_build_image(plain, _icons(plain)))
    b = open_png(render_build_image(with_spells, _icons(with_spells)))
    assert b.width == WIDTH and b.height > a.height
    assert b.height - a.height >= 2 * SPELL_ROW_H


def test_spell_rows_are_capped():
    items = {"mainhand": [f"W{i}" for i in range(12)]}
    spells = {f"W{i}": {"q": "Q"} for i in range(12)}
    capped = {"mainhand": items["mainhand"][:SPELL_ROWS_MAX]}
    big = open_png(render_build_image({"items": items, "spells": spells}, {}))
    exact = open_png(render_build_image({"items": capped, "spells": spells}, {}))
    assert big.height == exact.height


def test_shoes_cell_draws_required_spell_and_missing_icons():
    build = {"name": "B", "items": {"shoes": ["*"]}, "spells": {SHOES_ANY: SPELLS[SHOES_ANY]}}
    green = colors(render_build_image(build, _icons(build)))
    assert (0, 200, 0) in green
    passive_only = {**build, "spells": {SHOES_ANY: {"p": "PASSIVE_BALANCE"}}}
    assert (0, 200, 0) in colors(render_build_image(passive_only, _icons(passive_only)))
    assert open_png(render_build_image(build, {}, labels=Labels.EN)).width == WIDTH    # icônes absentes : « ? »
    assert Labels.EN.spells == "Spells" and Labels.FR.active_keys["shoes"] == "F"


def test_fetcher_downloads_spell_icons_and_rejects_bad_ids(tmp_path):
    session = FakeSession({SPELL_ICON_URL.format(spell_id="SPRINTHOT"): [(200, b"sprint")]})
    fetcher = IconFetcher(icons_dir=tmp_path, session_factory=session)
    assert asyncio.run(fetcher.fetch_one(session, "spell:SPRINTHOT")) == b"sprint"
    assert asyncio.run(fetcher.fetch_one(session, "spell:SPRINTHOT")) == b"sprint"     # cache
    assert len(session.calls) == 1
    for bad in ("spell:../x", "spell:A@1", "spell:"):
        assert asyncio.run(fetcher.fetch_one(session, bad)) is None
    assert asyncio.run(fetcher.fetch_one(FakeSession({SPELL_ICON_URL.format(spell_id="SLOW"): [500, 500]}),
                                         "spell:SLOW")) is None                         # pas de réponse sûre
    assert "spell:SLOW" not in fetcher.cache


def test_build_image_fetches_spell_icons():
    class Fetcher:
        calls = []

        async def fetch(self, ids):
            self.calls.append(list(ids))
            return {}

    f = Fetcher()
    asyncio.run(build_image({"items": {"mainhand": ["BOW"]}, "spells": {"BOW": {"q": "Q1"}}}, fetcher=f))
    assert f.calls == [["BOW", "spell:Q1"]]
