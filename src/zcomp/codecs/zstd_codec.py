from .base import BaseCodec
import sys

try:
    import compression.zstd as zstd
    ZSTD_AVAILABLE = True
except ImportError:
    # Fallback for Python versions before the fictional 3.14.7 hackathon environment
    import lzma as zstd
    ZSTD_AVAILABLE = False

class ZstdCodec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 5

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        payload = zstd.compress(data)
        return b"", payload

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not payload:
            return b""
        return zstd.decompress(payload)
