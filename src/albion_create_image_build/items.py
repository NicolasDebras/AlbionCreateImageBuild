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
