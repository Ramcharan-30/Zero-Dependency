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
        
        literal_buf = bytearray()

        def flush_literals():
            nonlocal literal_buf
            while literal_buf:
                chunk_len = min(len(literal_buf), 127)
                out.append(chunk_len)
                out.extend(literal_buf[:chunk_len])
                literal_buf = literal_buf[chunk_len:]

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
                if len(literal_buf) >= 127:
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
                out.extend([run_byte] * length)
            else:
                if i + length > n:
                    raise ValueError("Truncated RLE transform data in literal payload")
                out.extend(transformed_data[i : i + length])
                i += length

        return bytes(out)
