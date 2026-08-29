from .base import BaseTransform

class RleTransform(BaseTransform):
    """
    Reversible Run-Length Encoding Transform.
    Encodes byte streams into explicit Run (0x80 | len, byte) and Literal (len, bytes...) blocks.
    """
    @property
    def transform_id(self) -> int:
        return 2

    @property
    def name(self) -> str:
        return "RLE_TRANSFORM"

    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""

        out = bytearray()
        i = 0
        n = len(data)

        # Use an index pointer instead of re-slicing bytearray on flush
        literal_buf = bytearray()
        lit_start = 0

        def flush_literals():
            nonlocal lit_start
            while lit_start < len(literal_buf):
                chunk_len = min(len(literal_buf) - lit_start, 127)
                out.append(chunk_len)
                out.extend(literal_buf[lit_start : lit_start + chunk_len])
                lit_start += chunk_len
            literal_buf.clear()
            lit_start = 0

        while i < n:
            # Check for run of same byte starting at i
            run_byte = data[i]
            run_len = 1
            while i + run_len < n and data[i + run_len] == run_byte and run_len < 127:
                run_len += 1

            if run_len >= 4:
                # Flush pending literals first
                flush_literals()
                # Write run block
                out.append(0x80 | run_len)
                out.append(run_byte)
                i += run_len
            else:
                literal_buf.append(data[i])
                i += 1
                if len(literal_buf) - lit_start >= 127:
                    flush_literals()

        flush_literals()
        return b"", bytes(out)

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b""

        out = bytearray()
        i = 0
        n = len(transformed_data)

        while i < n:
            header = transformed_data[i]
            i += 1
            is_run = bool(header & 0x80)
            length = header & 0x7F

            if length == 0:
                raise ValueError("Corrupt RLE transform data: zero length header")

            if is_run:
                if i >= n:
                    raise ValueError("Truncated RLE transform data in run payload")
                run_byte = transformed_data[i]
                i += 1
                out.extend(bytes([run_byte]) * length)
            else:
                if i + length > n:
                    raise ValueError("Truncated RLE transform data in literal payload")
                out.extend(transformed_data[i : i + length])
                i += length

        return bytes(out)
