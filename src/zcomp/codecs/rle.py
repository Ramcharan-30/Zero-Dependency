from .base import BaseCodec

class RleCodec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 2

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        
        out = bytearray()
        i = 0
        n = len(data)
        
        while i < n:
            count = 1
            while i + 1 < n and data[i] == data[i+1] and count < 255:
                count += 1
                i += 1
            out.append(count)
            out.append(data[i])
            i += 1
            
        return b"", bytes(out)

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not payload:
            return b""
            
        out = bytearray()
        i = 0
        while i < len(payload):
            count = payload[i]
            char = payload[i+1]
            out.extend([char] * count)
            i += 2
            
        return bytes(out)
