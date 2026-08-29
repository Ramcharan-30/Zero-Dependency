import bz2
from .base import BaseCodec

class Bz2Codec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 6

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        payload = bz2.compress(data)
        return b"", payload

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not payload:
            return b""
        return bz2.decompress(payload)
