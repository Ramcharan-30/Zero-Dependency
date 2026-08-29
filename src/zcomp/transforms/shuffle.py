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
        aligned_end = n_words * 4

        # Stride slicing: collect every 4th byte starting at offset 0, 1, 2, 3
        plane0 = data[0:aligned_end:4]
        plane1 = data[1:aligned_end:4]
        plane2 = data[2:aligned_end:4]
        plane3 = data[3:aligned_end:4]

        out = plane0 + plane1 + plane2 + plane3
        if aligned_end < len(data):
            out += data[aligned_end:]

        meta = struct.pack("!I", len(data))
        return meta, out

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

        # Interleave planes back into original byte order
        out = bytearray(orig_len)
        out[0:n_words * 4:4] = plane0
        out[1:n_words * 4:4] = plane1
        out[2:n_words * 4:4] = plane2
        out[3:n_words * 4:4] = plane3

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
        aligned_end = n_words * 8

        # Stride slicing: collect every 8th byte starting at each offset
        planes = [data[p:aligned_end:8] for p in range(8)]

        out = b"".join(planes)
        if aligned_end < len(data):
            out += data[aligned_end:]

        meta = struct.pack("!I", len(data))
        return meta, out

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b""

        orig_len = struct.unpack("!I", meta)[0]
        n_words = orig_len // 8
        remainder = orig_len % 8

        planes = [transformed_data[p * n_words : (p + 1) * n_words] for p in range(8)]
        tail = transformed_data[8 * n_words :]

        # Interleave planes back into original byte order
        out = bytearray(orig_len)
        for p in range(8):
            out[p:n_words * 8:8] = planes[p]

        if remainder:
            out[n_words * 8 :] = tail

        return bytes(out)
