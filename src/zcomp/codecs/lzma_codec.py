import lzma
from .base import BaseCodec

class LzmaCodec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 4

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        payload = lzma.compress(data)
        return b"", payload

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not payload:
            return b""
        return lzma.decompress(payload)
