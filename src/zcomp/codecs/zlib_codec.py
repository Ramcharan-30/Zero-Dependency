import zlib
from .base import BaseCodec

class ZlibCodec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 3

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        payload = zlib.compress(data)
        return b"", payload

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not payload:
            return b""
        return zlib.decompress(payload)
