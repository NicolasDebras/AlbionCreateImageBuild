"""Outils de test : PNG unis, ouverture d'image, faux CDN (aucun réseau réel)."""
import asyncio
import io

from PIL import Image


def png(color=(200, 0, 0), size=128) -> bytes:
    out = io.BytesIO()
    Image.new("RGBA", (size, size), color).save(out, format="PNG")
    return out.getvalue()


def open_png(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data))


def colors(data: bytes, step: int = 2) -> set:
    img = open_png(data).convert("RGB")
    return {img.getpixel((x, y)) for x in range(0, img.width, step) for y in range(0, img.height, step)}


class FakeStream:
    """Comme aiohttp : read(n) rend ce qui est arrivé (paquets de NET_CHUNK octets max), b"" à la fin."""
    NET_CHUNK = 4096

    def __init__(self, body):
        self._body = body
        self._pos = 0

    async def read(self, n=-1):
        size = self.NET_CHUNK if n < 0 else min(n, self.NET_CHUNK)
        chunk = self._body[self._pos:self._pos + size]
        self._pos += len(chunk)
        return chunk


class FakeResponse:
    def __init__(self, status, body=b"png"):
        self.status = status
        self.content = FakeStream(body)


class FakeSession:
    """`script` : url → réponses successives (int = statut, (statut, corps), Exception = levée) ; 404 sinon."""

    def __init__(self, script=None, delay=0):
        self.script = {k: list(v) for k, v in (script or {}).items()}
        self.calls = []
        self.delay = delay
        self.closed = False

    def __call__(self):            # utilisable comme session_factory d'IconFetcher
        return self

    def get(self, url, **kwargs):
        self.calls.append(url)
        step = self.script[url].pop(0) if self.script.get(url) else 404
        session = self

        class Ctx:
            async def __aenter__(self):
                if session.delay:
                    await asyncio.sleep(session.delay)
                if isinstance(step, BaseException):
                    raise step
                return FakeResponse(*step) if isinstance(step, tuple) else FakeResponse(step)

            async def __aexit__(self, *exc):
                return False
        return Ctx()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.closed = True
        return False
