import collections
import heapq
import struct
from .base import BaseCodec
from ..bitio import BitWriter, BitReader

class HuffmanNode:
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
    heap = []
    for char, freq in frequencies.items():
        heapq.heappush(heap, HuffmanNode(char=char, freq=freq))
    
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
    if root is None:
        return b""
    if root.char is not None:
        return b"1" + bytes([root.char])
    return b"0" + serialize_tree(root.left) + serialize_tree(root.right)

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
        
        writer = BitWriter()
        for byte in data:
            for bit in codes[byte]:
                writer.write_bit(int(bit))
                
        padding_bits = (8 - writer.bit_count) % 8
        meta = struct.pack("!B", padding_bits) + tree_data
        
        return meta, writer.flush()

    def decompress(self, meta: bytes, payload: bytes) -> bytes:
        if not meta and not payload:
            return b""
            
        padding_bits = meta[0]
        tree_data = meta[1:]
        
        data_iter = iter(tree_data)
        root = deserialize_tree(data_iter)
        
        if root is None:
            return b""
            
        reader = BitReader(payload)
        out = bytearray()
        
        node = root
        total_bits = len(payload) * 8 - padding_bits
        
        for _ in range(total_bits):
            bit = reader.read_bit()
            if bit == 0:
                node = node.left
            else:
                node = node.right
                
            if node.char is not None:
                out.append(node.char)
                node = root
                
        return bytes(out)
