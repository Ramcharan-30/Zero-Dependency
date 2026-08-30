from ..profiler import ContentProfile
from ..transforms import (
    IdentityTransform,
    Delta8Transform,
    RleTransform,
    Shuffle32Transform,
    Shuffle64Transform,
    MeshTransform,
    BaseTransform
)
from ..codecs import (
    StoreCodec,
    ZstdCodec,
    LzmaCodec,
    Bz2Codec,
    ZlibCodec,
    HuffmanCodec,
    RleCodec,
    BaseCodec
)

def generate_candidates(profile: ContentProfile) -> list[tuple[BaseTransform, BaseCodec]]:
    """
    Generates a targeted set of (Transform, Codec) candidate pairs based on content profiling.
    Avoids running unpromising combinations on high-entropy or pre-compressed data.
    """
    none_t = IdentityTransform()
    delta_t = Delta8Transform()
    rle_t = RleTransform()
    shuf32_t = Shuffle32Transform()
    shuf64_t = Shuffle64Transform()
    mesh_t = MeshTransform()

    store_c = StoreCodec()
    zstd_c = ZstdCodec()
    lzma_c = LzmaCodec()
    bz2_c = Bz2Codec()
    zlib_c = ZlibCodec()
    huff_c = HuffmanCodec()
    rle_c = RleCodec()

    candidates: list[tuple[BaseTransform, BaseCodec]] = []

    # 1. High entropy or pre-compressed (PNG, JPEG, MP4, ZIP, XZ, etc.)
    if profile.already_compressed or profile.high_entropy:
        candidates = [
            (none_t, store_c),
            (none_t, zstd_c)
        ]
        return candidates

    # 2. Text data
    if profile.is_text:
        candidates = [
            (none_t, store_c),
            (none_t, zstd_c),
            (none_t, lzma_c),
            (none_t, bz2_c),
            (none_t, zlib_c),
            (none_t, huff_c)
        ]
        return candidates

    # 3. Highly repetitive data
    if profile.is_repetitive:
        candidates = [
            (none_t, store_c),
            (none_t, zstd_c),
            (rle_t, zstd_c),
            (none_t, lzma_c),
            (none_t, rle_c)
        ]
        return candidates

    # 3.5 3D Mesh / Model data
    # (Checked before structured binary because it's a specific subset)
    if profile.profile_id == 7: # Profile.MESH3D
        candidates = [
            (none_t, store_c),
            (mesh_t, zstd_c),
            (mesh_t, lzma_c),
            (none_t, zstd_c),
            (shuf32_t, zstd_c)
        ]
        return candidates

    # 4. Structured binary / numeric data
    if profile.is_structured_binary:
        candidates = [
            (none_t, store_c),
            (none_t, zstd_c),
            (delta_t, zstd_c),
            (shuf32_t, zstd_c),
            (shuf64_t, zstd_c),
            (mesh_t, zstd_c),
            (none_t, lzma_c),
            (none_t, bz2_c)
        ]
        return candidates

    # 5. Default general candidate set
    candidates = [
        (none_t, store_c),
        (none_t, zstd_c),
        (delta_t, zstd_c),
        (rle_t, zstd_c),
        (shuf32_t, zstd_c),
        (mesh_t, zstd_c),
        (none_t, lzma_c),
        (none_t, bz2_c),
        (none_t, zlib_c),
        (none_t, huff_c),
        (none_t, rle_c)
    ]
    return candidates
