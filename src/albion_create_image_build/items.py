"""Lecture de l'équipement d'un build Albion (aucune dépendance au rendu ni au réseau).

Format accepté (celui du jeu pour les ids) :
    {"mainhand": ["T8_MAIN_SWORD@1", "2H_HOLYSTAFF"], "cape": ["*"], "swaps": ["T7_OFF_SHIELD"], ...}

- chaque case = 1 à 3 objets au choix ; ``["*"]`` = au choix du joueur ;
- ``"T8_MAIN_SWORD@1"`` impose le tier 8 et l'enchantement .1, l'id nu ``"MAIN_SWORD"`` laisse le tier libre ;
- l'ancien format ``{"mainhand": "ID"}`` et une chaîne JSON (colonne JSONB lue brute) sont acceptés.
"""
import json
import re
from collections.abc import Mapping
from typing import Union

FREE_CHOICE = "*"
SWAPS_KEY = "swaps"     # objets de rechange, n'importe quel emplacement
SWAPS_MAX = 6

# Disposition de l'inventaire du jeu (grille 3×3, case vide en haut à gauche)
LAYOUT: tuple[tuple[str | None, ...], ...] = (
    (None, "head", "cape"),
    ("mainhand", "armor", "offhand"),
    ("potion", "shoes", "food"),
)
SLOTS: tuple[str, ...] = ("mainhand", "offhand", "head", "armor", "shoes", "cape", "food", "potion")
# L'enchantement y change l'effet, pas la puissance : un tier imposé n'y signifie pas « stuff minimum »
TIER_FREE_SLOTS: tuple[str, ...] = ("food", "potion")

ItemsInput = Union[Mapping[str, "str | list[str] | None"], str, None]

_TIERED_RE = re.compile(r"^T([1-8])_([A-Z0-9_]+?)(?:@([1-4]))?$")


def split_tier(item_id: str) -> tuple[str, int | None, int]:
    """« T8_MAIN_SWORD@1 » → ("MAIN_SWORD", 8, 1) ; « MAIN_SWORD » (tier libre) → ("MAIN_SWORD", None, 0)."""
    match = _TIERED_RE.match(item_id or "")
    if not match:
        return item_id, None, 0
    return match.group(2), int(match.group(1)), int(match.group(3) or 0)


def normalize_items(items: ItemsInput) -> dict[str, list[str]]:
    """Équipement nettoyé : {case: [ids]} sans case vide (ancien format et JSON brut acceptés)."""
    if isinstance(items, str):
        items = json.loads(items or "{}")
    out: dict[str, list[str]] = {}
    for slot, value in (items or {}).items():
        choices = [value] if isinstance(value, str) else list(value or [])
        choices = [c for c in choices if c]
        if choices:
            out[slot] = choices
    return out


# ── Sorts : {id de base de l'objet: {emplacement: id du sort}} ──────────────
# Emplacements : q/w/e (arme), a (actif d'armure), p et p2 (passifs). SHOES_ANY = sort de bottes
# imposé, bottes au choix (case Bottes vide ou « au choix »).
SPELL_KEYS: tuple[str, ...] = ("q", "w", "e", "a", "p", "p2")
SPELL_SLOTS: tuple[str, ...] = ("mainhand", "head", "armor", "shoes")
SHOES_ANY = "@shoes"
SPELL_PREFIX = "spell:"   # clé d'icône d'un sort (« spell:SPRINTHOT »), à côté des ids d'objets

SpellsInput = Union[Mapping[str, Mapping[str, str]], str, None]


def normalize_spells(spells: SpellsInput) -> dict[str, dict[str, str]]:
    """Sorts nettoyés, dans l'ordre SPELL_KEYS, sans objet vide (JSON brut accepté)."""
    if isinstance(spells, str):
        spells = json.loads(spells or "{}")
    out: dict[str, dict[str, str]] = {}
    for key, chosen in (spells or {}).items():
        if isinstance(chosen, Mapping):
            clean = {k: chosen[k] for k in SPELL_KEYS if chosen.get(k)}
            if clean:
                out[key] = clean
    return out


def spell_rows(items: ItemsInput, spells: SpellsInput) -> list[tuple[str, str, dict[str, str]]]:
    """(case, id d'objet tel que choisi, sorts) de chaque objet du build qui a des sorts, dans
    l'ordre arme, tête, armure, bottes ; les sorts sont rangés par id de base de l'objet."""
    gear, chosen = normalize_items(items), normalize_spells(spells)
    rows = []
    for slot in SPELL_SLOTS:
        for item_id in gear.get(slot, []):
            if item_id != FREE_CHOICE and (s := chosen.get(split_tier(item_id)[0])):
                rows.append((slot, item_id, s))
    return rows


def shoes_any_spells(items: ItemsInput, spells: SpellsInput) -> dict[str, str]:
    """Sort de bottes imposé (bottes au choix), ou {} si une botte précise est choisie."""
    if any(c != FREE_CHOICE for c in normalize_items(items).get("shoes", [])):
        return {}
    return normalize_spells(spells).get(SHOES_ANY, {})


def spell_ids(items: ItemsInput, spells: SpellsInput) -> list[str]:
    """Clés d'icônes (« spell:<ID> ») des sorts dessinés, sans doublon."""
    seen: list[str] = []
    chosen = [s for _, _, s in spell_rows(items, spells)] + [shoes_any_spells(items, spells)]
    for s in chosen:
        for spell in s.values():
            if SPELL_PREFIX + spell not in seen:
                seen.append(SPELL_PREFIX + spell)
    return seen


def item_ids(items: ItemsInput) -> list[str]:
    """Ids d'objets dont il faut l'icône (ordre conservé, sans doublon, sans « au choix »)."""
    seen: list[str] = []
    for choices in normalize_items(items).values():
        for c in choices:
            if c != FREE_CHOICE and c not in seen:
                seen.append(c)
    return seen


def has_tiered_gear(items: ItemsInput) -> bool:
    """Vrai si au moins un équipement (hors bouffe/potion) impose un tier."""
    return any(split_tier(c)[1] is not None
               for slot, choices in normalize_items(items).items() if slot not in TIER_FREE_SLOTS
               for c in choices)
