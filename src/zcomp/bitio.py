class BitWriter:
    def __init__(self):
        self.accumulator = 0
        self.bit_count = 0
        self.out = bytearray()

    def write_bit(self, bit: int):
        self.accumulator = (self.accumulator << 1) | (bit & 1)
        self.bit_count += 1
        if self.bit_count == 8:
            self.out.append(self.accumulator)
            self.accumulator = 0
            self.bit_count = 0

    def flush(self) -> bytes:
        if self.bit_count > 0:
            self.accumulator <<= (8 - self.bit_count)
            self.out.append(self.accumulator)
            self.accumulator = 0
            self.bit_count = 0
        return bytes(self.out)

class BitReader:
    def __init__(self, data: bytes):
        self.data = data
        self.byte_index = 0
        self.bit_index = 0
        self.length = len(data)

    def read_bit(self) -> int:
        if self.byte_index >= self.length:
            raise EOFError("Unexpected end of bit stream")
        bit = (self.data[self.byte_index] >> (7 - self.bit_index)) & 1
        self.bit_index += 1
        if self.bit_index == 8:
            self.bit_index = 0
            self.byte_index += 1
        return bit
