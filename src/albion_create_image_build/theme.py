"""Couleurs des images et rôles connus. Le thème par défaut (noir & lilas) est celui de Lilium.

Exemple : ``Theme(accent=(255, 80, 80), role_colors={**DEFAULT_THEME.role_colors, "SCOUT": (240, 200, 0)})``.
"""
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

RGB = tuple[int, int, int]

# Pictogrammes de rôle disponibles (dessinés par la lib) ; un rôle sans pictogramme a une pastille ronde.
ROLE_SHAPES = ("swords", "shield", "cross", "star", "dot")


def _frozen(d: dict) -> Mapping:
    return field(default_factory=lambda: MappingProxyType(dict(d)))


@dataclass(frozen=True)
class Theme:
    background: RGB = (11, 10, 15)
    surface: RGB = (31, 27, 41)        # fond des cases
    border: RGB = (46, 40, 64)         # contour d'une case vide
    accent: RGB = (200, 162, 255)      # titre, cases remplies, haut du dégradé de la compo
    accent_dark: RGB = (167, 123, 243)  # bas du dégradé de la compo
    ink: RGB = (20, 15, 31)            # texte sombre sur le fond de la compo
    text: RGB = (236, 232, 245)
    muted: RGB = (157, 149, 179)
    # Bord de la pastille « 8.1 » selon l'enchantement, comme en jeu (.0 neutre, .1 vert, .2 bleu, .3 violet, .4 or)
    enchant_colors: Mapping[int, RGB] = _frozen(
        {0: (157, 149, 179), 1: (92, 201, 112), 2: (88, 160, 255), 3: (184, 120, 255), 4: (255, 200, 80)})
    # Rôles connus, dans l'ordre d'affichage de la compo ; les autres rôles viennent après.
    role_order: tuple[str, ...] = ("TANK", "HEAL", "SUPPORT", "DPS")
    role_colors: Mapping[str, RGB] = _frozen(
        {"TANK": (57, 135, 229), "HEAL": (25, 158, 112), "DPS": (217, 89, 38), "SUPPORT": (144, 133, 233)})
    role_other_color: RGB = (98, 92, 120)
    role_shapes: Mapping[str, str] = _frozen({"DPS": "swords", "TANK": "shield", "HEAL": "cross", "SUPPORT": "star"})

    def base_role(self, role: str) -> str:
        """« TANK · Main tank » → « TANK » ; « TANK 2 » (ligne en double) → « TANK » si TANK est un rôle connu."""
        base = role.split(" · ", 1)[0].strip()
        unnumbered = re.sub(r" \d+$", "", base)
        return unnumbered if unnumbered in self.role_order else base

    def role_rank(self, role: str) -> int:
        """Position du rôle dans ``role_order`` (les rôles inconnus après)."""
        base = self.base_role(role)
        return self.role_order.index(base) if base in self.role_order else len(self.role_order)

    def role_color(self, role: str) -> RGB:
        return self.role_colors.get(self.base_role(role), self.role_other_color)

    def role_shape(self, role: str) -> str:
        return self.role_shapes.get(self.base_role(role), "dot")


DEFAULT_THEME = Theme()


def role_rank(role: str, theme: Theme = DEFAULT_THEME) -> int:
    return theme.role_rank(role)


def role_color(role: str, theme: Theme = DEFAULT_THEME) -> RGB:
    return theme.role_color(role)


def mix(a: RGB, b: RGB, t: float) -> RGB:
    """Couleur à `t` (0 → a, 1 → b) entre a et b."""
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b, strict=True))  # type: ignore[return-value]
