from .base import BaseCodec
from .store import StoreCodec
from .huffman import HuffmanCodec
from .rle import RleCodec
from .zlib_codec import ZlibCodec
from .lzma_codec import LzmaCodec
from .zstd_codec import ZstdCodec, ZSTD_AVAILABLE

def get_codec(algorithm_id: int) -> BaseCodec:
    codecs = {
        0: StoreCodec,
        1: HuffmanCodec,
        2: RleCodec,
        3: ZlibCodec,
        4: LzmaCodec,
        5: ZstdCodec
    }
    if algorithm_id not in codecs:
        raise ValueError(f"Unknown algorithm ID: {algorithm_id}")
    return codecs[algorithm_id]()

def get_all_codecs() -> list[BaseCodec]:
    return [
        ZstdCodec(),
        LzmaCodec(),
        ZlibCodec(),
        HuffmanCodec(),
        RleCodec(),
        StoreCodec()
    ]
