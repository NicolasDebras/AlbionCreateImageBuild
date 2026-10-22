"""IconFetcher : icônes locales, secours CDN, cache, limites — sans réseau réel (FakeSession)."""
import asyncio

import pytest
from helpers import FakeSession

from albion_create_image_build import IconFetcher, default_fetcher, local_icon
from albion_create_image_build.icons import ICON_URL_EXACT, ICON_URL_TIER


def url(tier, item_id):
    return ICON_URL_TIER.format(tier=tier, item_id=item_id)


def exact(item_id):
    return ICON_URL_EXACT.format(item_id=item_id)


@pytest.fixture
def fetcher(tmp_path):
    """Dossier d'icônes locales vide : ces tests visent le secours CDN."""
    return IconFetcher(icons_dir=tmp_path)


def one(fetcher, session, item_id):
    return asyncio.run(fetcher.fetch_one(session, item_id))


# ── Icônes locales ───────────────────────────────────────────────────────────

def test_local_icon_is_used_without_network(tmp_path, fetcher):
    (tmp_path / "MAIN_MACE.png").write_bytes(b"local")
    session = FakeSession()
    assert one(fetcher, session, "MAIN_MACE") == b"local"
    assert session.calls == []


def test_local_icon_rejects_path_traversal(tmp_path):
    (tmp_path.parent / "secret.png").write_bytes(b"x")
    for bad in ("../secret", "..\\secret", "a/b", ""):
        assert local_icon(bad, tmp_path) is None


def test_without_icons_dir_everything_comes_from_the_cdn():
    fetcher = IconFetcher(icons_dir=None)
    session = FakeSession({url(8, "MAIN_MACE_HELL"): [200]})   # MAIN_MACE_HELL est pourtant embarquée
    assert one(fetcher, session, "MAIN_MACE_HELL") == b"png"
    assert session.calls == [url(8, "MAIN_MACE_HELL")]


# ── Secours CDN ──────────────────────────────────────────────────────────────

def test_falls_back_to_lower_tier_and_caches(fetcher):
    session = FakeSession({url(8, "MEAL_OMELETTE"): [404], url(7, "MEAL_OMELETTE"): [200]})
    assert one(fetcher, session, "MEAL_OMELETTE") == b"png"
    assert one(fetcher, session, "MEAL_OMELETTE") == b"png"
    assert len(session.calls) == 2   # 2e appel servi par le cache


def test_retries_after_timeout(fetcher):
    assert one(fetcher, FakeSession({url(8, "A"): [TimeoutError(), 200]}), "A") == b"png"


def test_transient_failure_is_not_cached(fetcher):
    """Un CDN lent ne doit pas marquer l'icône comme absente pour toujours."""
    session = FakeSession({url(8, "A"): [TimeoutError()] * fetcher.retries})
    assert one(fetcher, session, "A") is None
    assert "A" not in fetcher.cache


def test_server_error_is_not_a_sure_answer(fetcher):
    session = FakeSession({url(8, "A"): [500, 503]})
    assert one(fetcher, session, "A") is None
    assert "A" not in fetcher.cache


def test_tiered_item_uses_exact_icon_first(tmp_path, fetcher):
    (tmp_path / "MAIN_SWORD.png").write_bytes(b"local")
    session = FakeSession({exact("T7_MAIN_SWORD@2"): [(200, b"t72")]})
    assert one(fetcher, session, "T7_MAIN_SWORD@2") == b"t72"
    assert session.calls == [exact("T7_MAIN_SWORD@2")]
    assert fetcher.cache["T7_MAIN_SWORD@2"] == b"t72"


def test_tiered_item_missing_on_cdn_falls_back_to_base_icon(tmp_path, fetcher):
    (tmp_path / "MAIN_SWORD.png").write_bytes(b"local")
    assert one(fetcher, FakeSession(), "T6_MAIN_SWORD@4") == b"local"   # 404 sur l'URL exacte
    session = FakeSession({url(8, "OFF_SHIELD"): [200]})
    assert one(fetcher, session, "T6_OFF_SHIELD@1") == b"png"
    assert session.calls[-1] == url(8, "OFF_SHIELD")


def test_tiered_item_with_slow_cdn_is_not_cached(fetcher):
    session = FakeSession({exact("T8_A"): [TimeoutError()] * fetcher.retries})
    assert one(fetcher, session, "T8_A") is None
    assert "T8_A" not in fetcher.cache


def test_unknown_item_is_cached_as_missing(fetcher):
    session = FakeSession()
    assert one(fetcher, session, "INCONNU") is None
    assert fetcher.cache["INCONNU"] is None
    assert len(session.calls) == 8   # T8 → T1


def test_ignores_oversized_body(fetcher):
    """Une réponse anormalement grosse n'est ni chargée en entier ni gardée."""
    big = b"x" * (fetcher.max_bytes + 10)
    assert one(fetcher, FakeSession({url(8, "A"): [(200, big)]}), "A") is None


def test_icon_larger_than_one_network_chunk_is_read_entirely(fetcher):
    """Régression : read(n) seul ne rendait que le 1er paquet → PNG tronqué, dessiné « ? »."""
    body = bytes(range(256)) * 100   # 25,6 Ko, comme une vraie icône 128 px
    session = FakeSession({exact("T6_2H_CROSSBOW@4"): [(200, body)]})
    assert one(fetcher, session, "T6_2H_CROSSBOW@4") == body


def test_rejects_malformed_item_id_without_network(fetcher):
    session = FakeSession()
    for bad in ("../../x", "A?size=99999", "a b", "", "A/B", "X" * 81):
        assert one(fetcher, session, bad) is None
    assert session.calls == []


def test_cache_is_bounded(fetcher):
    fetcher.cache_max = 3
    session = FakeSession({url(8, i): [200] for i in "ABCD"})
    for i in "ABCD":
        one(fetcher, session, i)
    assert len(fetcher.cache) <= 3 and "D" in fetcher.cache


def test_each_fetcher_has_its_own_cache(tmp_path):
    a, b = IconFetcher(icons_dir=tmp_path), IconFetcher(icons_dir=tmp_path)
    one(a, FakeSession({url(8, "A"): [200]}), "A")
    assert "A" in a.cache and "A" not in b.cache


def test_default_fetcher_is_shared():
    assert default_fetcher() is default_fetcher()
    assert isinstance(default_fetcher(), IconFetcher)


# ── fetch (plusieurs icônes) ─────────────────────────────────────────────────

def test_fetch_uses_the_session_factory_and_dedupes(tmp_path):
    session = FakeSession({url(8, "A"): [200], url(8, "B"): [(200, b"b")]})
    fetcher = IconFetcher(icons_dir=tmp_path, session_factory=session)
    icons = asyncio.run(fetcher.fetch(["A", "B", "A", "INCONNU"]))
    assert icons == {"A": b"png", "B": b"b", "INCONNU": None}
    assert session.closed


def test_fetch_never_raises_and_limits_concurrency(fetcher):
    running, peak = 0, 0

    async def slow(session, item_id):
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.01)
        running -= 1
        if item_id == "BOOM":
            raise RuntimeError("panne")
        return b"png"

    fetcher.fetch_one = slow
    fetcher.session_factory = FakeSession()
    icons = asyncio.run(fetcher.fetch([f"I{n}" for n in range(20)] + ["BOOM"]))
    assert icons["BOOM"] is None
    assert all(icons[f"I{n}"] == b"png" for n in range(20))
    assert peak <= fetcher.concurrency


def test_fetch_deadline_turns_slow_icons_into_none(fetcher):
    async def fetch(session, item_id):
        await asyncio.sleep(5 if item_id == "LENT" else 0)
        return b"png"

    fetcher.fetch_one = fetch
    fetcher.session_factory = FakeSession()
    fetcher.deadline = 0.2
    assert asyncio.run(fetcher.fetch(["OK", "LENT"])) == {"OK": b"png", "LENT": None}


def test_fetch_empty_opens_no_session(fetcher):
    def no_session():
        raise AssertionError("aucune session ne doit être ouverte")

    fetcher.session_factory = no_session
    assert asyncio.run(fetcher.fetch([])) == {}
