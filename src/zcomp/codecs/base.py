class BaseCodec:
    @property
    def algorithm_id(self) -> int:
        raise NotImplementedError

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        """Returns (metadata, payload)"""
        raise NotImplementedError

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        raise NotImplementedError
