"""Textes dessinés sur les images. Français par défaut (``Labels.FR``), anglais : ``Labels.EN``.

Personnaliser : ``dataclasses.replace(Labels.EN, free_choice="Any")``.
"""
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import ClassVar


@dataclass(frozen=True)
class Labels:
    slots: Mapping[str, str]                 # nom de chaque case de l'inventaire
    free_choice: str                         # case « au choix du joueur » (image du build)
    free_choice_lines: tuple[str, str]       # idem sur 2 lignes (petites cases de la compo)
    n_choices: str                           # « {n} au choix » sous une case à plusieurs objets
    swaps: str                               # titre de la colonne des objets de rechange
    compo_header: str                        # « {players} joueurs · {builds} builds »
    untitled: str                            # build sans nom
    spells: str = "Sorts"                    # titre de la section des sorts (image du build)
    # Touche de chaque emplacement de sort ; l'actif d'armure prend la touche du jeu (D, R, F)
    spell_keys: Mapping[str, str] = MappingProxyType({"q": "Q", "w": "W", "e": "E", "p": "P", "p2": "P2"})
    active_keys: Mapping[str, str] = MappingProxyType({"head": "D", "armor": "R", "shoes": "F"})

    FR: ClassVar["Labels"]
    EN: ClassVar["Labels"]


Labels.FR = Labels(
    slots=MappingProxyType({"mainhand": "Arme", "offhand": "Main gauche", "head": "Tête", "armor": "Armure",
                            "shoes": "Bottes", "cape": "Cape", "food": "Bouffe", "potion": "Potion"}),
    free_choice="Au choix",
    free_choice_lines=("Au", "choix"),
    n_choices="{n} au choix",
    swaps="Swaps",
    compo_header="{players} joueurs · {builds} builds",
    untitled="Build",
)

Labels.EN = Labels(
    slots=MappingProxyType({"mainhand": "Weapon", "offhand": "Off-hand", "head": "Head", "armor": "Armor",
                            "shoes": "Shoes", "cape": "Cape", "food": "Food", "potion": "Potion"}),
    free_choice="Free pick",
    free_choice_lines=("Free", "pick"),
    n_choices="{n} options",
    swaps="Swaps",
    compo_header="{players} players · {builds} builds",
    untitled="Build",
    spells="Spells",
)
