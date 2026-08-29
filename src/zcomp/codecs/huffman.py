import collections
import heapq
import struct
from .base import BaseCodec

class HuffmanNode:
    __slots__ = ('char', 'freq', 'left', 'right')

    def __init__(self, char=None, freq=0, left=None, right=None):
        self.char = char
        self.freq = freq
        self.left = left
        self.right = right

    def __lt__(self, other):
        if self.freq == other.freq:
            if self.char is not None and other.char is not None:
                return self.char < other.char
            return id(self) < id(other)
        return self.freq < other.freq

def build_tree(frequencies):
    heap = [HuffmanNode(char=char, freq=freq) for char, freq in frequencies.items()]
    heapq.heapify(heap)

    if not heap:
        return None

    if len(heap) == 1:
        node = heapq.heappop(heap)
        root = HuffmanNode(freq=node.freq)
        root.left = node
        return root

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = HuffmanNode(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    return heapq.heappop(heap)

def generate_codes(root, current_code="", codes=None):
    if codes is None:
        codes = {}
    if root is None:
        return codes
    if root.char is not None:
        codes[root.char] = current_code
        return codes
    generate_codes(root.left, current_code + "0", codes)
    generate_codes(root.right, current_code + "1", codes)
    return codes

def serialize_tree(root):
    """Serialize tree iteratively using a stack to avoid recursion depth limits."""
    if root is None:
        return b""
    parts = []
    stack = [root]
    while stack:
        node = stack.pop()
        if node.char is not None:
            parts.append(b"1")
            parts.append(bytes([node.char]))
        else:
            parts.append(b"0")
            # Push right first so left is processed first (stack is LIFO)
            if node.right is not None:
                stack.append(node.right)
            if node.left is not None:
                stack.append(node.left)
    return b"".join(parts)

def deserialize_tree(data_iter):
    try:
        bit = next(data_iter)
        if bit == ord(b'1'):
            char = next(data_iter)
            return HuffmanNode(char=char)
        else:
            left = deserialize_tree(data_iter)
            right = deserialize_tree(data_iter)
            return HuffmanNode(left=left, right=right)
    except StopIteration:
        return None


class HuffmanCodec(BaseCodec):
    @property
    def algorithm_id(self) -> int:
        return 1

    def compress(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b"", b""

        freqs = collections.Counter(data)
        root = build_tree(freqs)
        codes = generate_codes(root)

        tree_data = serialize_tree(root)

        # Pre-compute integer code table: byte_value -> (int_code, bit_length)
        int_codes = {}
        for byte_val, code_str in codes.items():
            if code_str:
                int_codes[byte_val] = (int(code_str, 2), len(code_str))
            else:
                int_codes[byte_val] = (0, 1)

        # Batch bit-packing: accumulate into a large integer, then convert to bytes
        accumulator = 0
        total_bits = 0
        for byte_val in data:
            code_int, code_len = int_codes[byte_val]
            accumulator = (accumulator << code_len) | code_int
            total_bits += code_len

        # Pad to byte boundary
        padding_bits = (8 - total_bits % 8) % 8
        accumulator <<= padding_bits
        total_bits += padding_bits

        # Convert the large integer to bytes
        num_bytes = total_bits // 8
        if num_bytes > 0:
            payload = accumulator.to_bytes(num_bytes, 'big')
        else:
            payload = b""

        meta = struct.pack("!B", padding_bits) + tree_data
        return meta, payload

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not meta and not payload:
            return b""

        padding_bits = meta[0]
        tree_data = meta[1:]

        data_iter = iter(tree_data)
        root = deserialize_tree(data_iter)

        if root is None:
            return b""

        # Fast path: single-symbol tree (only one unique byte in original data)
        if root.left is not None and root.left.char is not None and root.right is None:
            total_bits = len(payload) * 8 - padding_bits
            return bytes([root.left.char] * total_bits)

        # Bit-by-bit tree walk using inlined index arithmetic (no BitReader overhead)
        total_bits = len(payload) * 8 - padding_bits
        out = bytearray()

        node = root
        byte_idx = 0
        bit_idx = 7  # MSB first

        for _ in range(total_bits):
            bit = (payload[byte_idx] >> bit_idx) & 1
            bit_idx -= 1
            if bit_idx < 0:
                bit_idx = 7
                byte_idx += 1

            if bit == 0:
                node = node.left
            else:
                node = node.right

            if node.char is not None:
                out.append(node.char)
                node = root

        return bytes(out)
