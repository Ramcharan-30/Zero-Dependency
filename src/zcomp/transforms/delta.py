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
        
        out = bytearray(len(data))
        out[0] = data[0]
        for i in range(1, len(data)):
            out[i] = (data[i] - data[i - 1]) & 0xFF
            
        return b"", bytes(out)

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b""
        
        out = bytearray(len(transformed_data))
        out[0] = transformed_data[0]
        for i in range(1, len(transformed_data)):
            out[i] = (out[i - 1] + transformed_data[i]) & 0xFF
            
        return bytes(out)
