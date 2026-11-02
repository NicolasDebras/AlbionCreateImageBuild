"""IconImages : icônes d'un rendu décodées une fois, redimensionnées une fois par taille."""
from helpers import png
from PIL import Image

from albion_create_image_build._draw import IconImages


def test_icon_is_decoded_once_and_resized_once_per_size(monkeypatch):
    opened = []
    real_open = Image.open
    monkeypatch.setattr(Image, "open", lambda f: opened.append(1) or real_open(f))
    images = IconImages({"A": png((10, 20, 30, 255))})
    small, big = images.get("A", 22), images.get("A", 52)
    assert images.get("A", 22) is small and images.get("A", 52) is big
    assert small.size == (22, 22) and big.size == (52, 52) and small.mode == "RGBA"
    assert big.getpixel((26, 26)) == (10, 20, 30, 255)
    assert len(opened) == 1


def test_missing_or_unreadable_icon_is_none():
    images = IconImages({"VIDE": None, "CASSE": b"pas un png"})
    assert images.get("VIDE", 52) is None
    assert images.get("CASSE", 52) is None
    assert images.get("ABSENT", 52) is None
