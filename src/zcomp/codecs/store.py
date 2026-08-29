from .base import BaseCodec

class StoreCodec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 0

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        return b"", data

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        return payload
