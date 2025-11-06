import zlib
from typing import ByteString

_ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz-_"


def _encode6bit(b: int) -> str:
    if b < 0:
        b = 0
    if b < 64:
        return _ALPHABET[b]
    return "?"


def _append3bytes(b1: int, b2: int, b3: int) -> str:
    c1 = (b1 >> 2) & 0x3F
    c2 = ((b1 & 0x3) << 4 | (b2 >> 4)) & 0x3F
    c3 = ((b2 & 0xF) << 2 | (b3 >> 6)) & 0x3F
    c4 = b3 & 0x3F
    return (
            _encode6bit(c1) +
            _encode6bit(c2) +
            _encode6bit(c3) +
            _encode6bit(c4)
    )


def plantuml_deflate(data: ByteString) -> bytes:
    co = zlib.compressobj(level=9, wbits=-15)  # raw DEFLATE (no zlib header/trailer)
    return co.compress(data) + co.flush()


def plantuml_encode(data: bytes) -> str:
    res = []
    i = 0
    n = len(data)
    while i < n:
        b1 = data[i]
        i += 1
        b2 = data[i] if i < n else 0
        i += 1 if i < n else 0
        b3 = data[i] if i < n else 0
        i += 1 if i < n else 0

        block = _append3bytes(b1, b2, b3)
        # Trim padding per PlantUML rules (no '=' padding; shorten last block)
        if i - 1 >= n:      # we used fake b3
            block = block[:3]
        if i - 2 >= n:      # we used fake b2 (and b3)
            block = block[:2]
        res.append(block)
    return "".join(res)


def plantuml_url(text: str, server: str = "https://uml.planttext.com/plantuml/png") -> str:
    compressed = plantuml_deflate(text.encode("utf-8"))
    encoded = plantuml_encode(compressed)
    return f"{server}/{encoded}"
