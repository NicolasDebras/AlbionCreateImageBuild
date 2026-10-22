"""build_image / compo_image : icônes demandées au fetcher, rendu dans un thread."""
import asyncio

from helpers import open_png, png

from albion_create_image_build import COMPO_MAX_ROWS, WIDTH, Labels, build_image, compo_image, icons


class FakeFetcher:
    def __init__(self):
        self.calls = []

    async def fetch(self, ids):
        ids = list(ids)
        self.calls.append(ids)
        return {i: png() for i in ids}


def test_build_image_fetches_icons_then_renders():
    fetcher = FakeFetcher()
    build = {"name": "B", "items": {"mainhand": ["A", "B"], "cape": ["*"], "swaps": ["A", "C"]}}
    data = asyncio.run(build_image(build, fetcher=fetcher, signature="S", labels=Labels.EN))
    assert fetcher.calls == [["A", "B", "C"]]
    assert open_png(data).width > WIDTH   # swaps


def test_compo_image_none_without_rows():
    fetcher = FakeFetcher()
    assert asyncio.run(compo_image([], fetcher=fetcher)) is None
    assert fetcher.calls == []


def test_compo_image_fetches_each_icon_once_across_builds():
    fetcher = FakeFetcher()
    rows = [("Party 1", "TANK", 1, {"name": "T", "items": {"mainhand": ["MACE"]}}),
            ("Party 1", "DPS", 3, {"name": "D", "items": '{"mainhand": ["MACE", "BOW"]}'})]
    assert open_png(asyncio.run(compo_image(rows, fetcher=fetcher))).format == "PNG"
    assert fetcher.calls == [["MACE", "BOW"]]


def test_compo_image_only_fetches_icons_of_drawn_rows():
    fetcher = FakeFetcher()
    rows = [("P", "DPS", 1, {"name": str(i), "items": {"mainhand": [f"I{i}"]}}) for i in range(COMPO_MAX_ROWS + 5)]
    asyncio.run(compo_image(rows, fetcher=fetcher))
    assert len(fetcher.calls[0]) == COMPO_MAX_ROWS


def test_default_fetcher_is_used_when_none_given(monkeypatch):
    fake = FakeFetcher()
    monkeypatch.setattr(icons, "_default", fake)
    asyncio.run(build_image({"name": "B", "items": {"head": ["H"]}}))
    assert fake.calls == [["H"]]
