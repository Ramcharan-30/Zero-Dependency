import struct
from .base import BaseTransform

class Shuffle32Transform(BaseTransform):
    """
    Byte-plane shuffling transform for 32-bit (4-byte) structured records.
    Separates 4-byte integers into 4 low-variance byte planes.
    """
    @property
    def transform_id(self) -> int:
        return 3

    @property
    def name(self) -> str:
        return "SHUFFLE32"

    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        
        n_words = len(data) // 4
        remainder = len(data) % 4
        
        planes = [bytearray(n_words) for _ in range(4)]
        for i in range(n_words):
            offset = i * 4
            planes[0][i] = data[offset]
            planes[1][i] = data[offset + 1]
            planes[2][i] = data[offset + 2]
            planes[3][i] = data[offset + 3]
            
        out = bytearray()
        for plane in planes:
            out.extend(plane)
        if remainder:
            out.extend(data[n_words * 4:])
            
        meta = struct.pack("!I", len(data))
        return meta, bytes(out)

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b""
        
        orig_len = struct.unpack("!I", meta)[0]
        n_words = orig_len // 4
        remainder = orig_len % 4
        
        plane0 = transformed_data[:n_words]
        plane1 = transformed_data[n_words : 2 * n_words]
        plane2 = transformed_data[2 * n_words : 3 * n_words]
        plane3 = transformed_data[3 * n_words : 4 * n_words]
        tail = transformed_data[4 * n_words :]
        
        out = bytearray(orig_len)
        for i in range(n_words):
            offset = i * 4
            out[offset] = plane0[i]
            out[offset + 1] = plane1[i]
            out[offset + 2] = plane2[i]
            out[offset + 3] = plane3[i]
            
        if remainder:
            out[n_words * 4 :] = tail
            
        return bytes(out)


class Shuffle64Transform(BaseTransform):
    """
    Byte-plane shuffling transform for 64-bit (8-byte) structured records.
    Separates 8-byte integers into 8 low-variance byte planes.
    """
    @property
    def transform_id(self) -> int:
        return 4

    @property
    def name(self) -> str:
        return "SHUFFLE64"

    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""
        
        n_words = len(data) // 8
        remainder = len(data) % 8
        
        planes = [bytearray(n_words) for _ in range(8)]
        for i in range(n_words):
            offset = i * 8
            for p in range(8):
                planes[p][i] = data[offset + p]
            
        out = bytearray()
        for plane in planes:
            out.extend(plane)
        if remainder:
            out.extend(data[n_words * 8:])
            
        meta = struct.pack("!I", len(data))
        return meta, bytes(out)

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b""
        
        orig_len = struct.unpack("!I", meta)[0]
        n_words = orig_len // 8
        remainder = orig_len % 8
        
        planes = [transformed_data[p * n_words : (p + 1) * n_words] for p in range(8)]
        tail = transformed_data[8 * n_words :]
        
        out = bytearray(orig_len)
        for i in range(n_words):
            offset = i * 8
            for p in range(8):
                out[offset + p] = planes[p][i]
            
        if remainder:
            out[n_words * 8 :] = tail
            
        return bytes(out)
