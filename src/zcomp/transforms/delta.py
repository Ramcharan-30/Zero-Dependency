from array import array
from .base import BaseTransform

class Delta8Transform(BaseTransform):
    @property
    def transform_id(self) -> int:
        return 1

    @property
    def name(self) -> str:
        return "DELTA8"

    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""

        # Use array module for fast element-wise access
        src = array('B', data)
        n = len(src)
        out = array('B', bytes(n))
        out[0] = src[0]
        for i in range(1, n):
            out[i] = (src[i] - src[i - 1]) & 0xFF

        return b"", out.tobytes()

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b""

        src = array('B', transformed_data)
        n = len(src)
        out = array('B', bytes(n))
        out[0] = src[0]
        for i in range(1, n):
            out[i] = (out[i - 1] + src[i]) & 0xFF

        return out.tobytes()
