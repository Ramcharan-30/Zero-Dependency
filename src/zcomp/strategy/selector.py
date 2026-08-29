import struct
from pathlib import Path
from dataclasses import dataclass
from ..profiler import ContentProfile
from ..transforms import BaseTransform, IdentityTransform
from ..codecs import BaseCodec, StoreCodec
from ..archive import serialize_archive, compute_archive_size
from ..verification import compute_crc32, compute_sha256
from .candidates import generate_candidates

@dataclass
class CandidateEvaluation:
    transform_name: str
    codec_name: str
    display_label: str
    archive_size: int
    is_winner: bool = False

@dataclass
class CandidateSelectionResult:
    best_archive_bytes: bytes
    best_transform: BaseTransform
    best_codec: BaseCodec
    best_size: int
    evaluations: list[CandidateEvaluation]

def pack_combined_metadata(trans_meta: bytes, codec_meta: bytes) -> bytes:
    """Packs transform metadata and codec metadata into a single byte array."""
    return struct.pack("!H", len(trans_meta)) + trans_meta + struct.pack("!H", len(codec_meta)) + codec_meta

def unpack_combined_metadata(full_meta: bytes) -> tuple[bytes, bytes]:
    """Unpacks transform metadata and codec metadata from combined metadata bytes."""
    if len(full_meta) < 4:
        return b"", full_meta
    try:
        trans_len = struct.unpack("!H", full_meta[:2])[0]
        if len(full_meta) < 4 + trans_len:
            return b"", full_meta
        trans_meta = full_meta[2 : 2 + trans_len]
        codec_len = struct.unpack("!H", full_meta[2 + trans_len : 4 + trans_len])[0]
        codec_meta = full_meta[4 + trans_len : 4 + trans_len + codec_len]
        return trans_meta, codec_meta
    except Exception:
        return b"", full_meta

def select_best_candidate(
    original_filename: str,
    data: bytes,
    profile: ContentProfile,
    profile_id: int = 255
) -> CandidateSelectionResult:
    """
    Evaluates candidate (Transform, Codec) pairs by computing .ZC archive sizes
    and selects the candidate that produces the SMALLEST VALID COMPLETE .ZC ARCHIVE.

    Optimized: checksums are computed once and archive sizes are calculated
    arithmetically. Only the winning candidate is fully serialized.
    """
    candidates = generate_candidates(profile)
    evaluations: list[CandidateEvaluation] = []

    # Pre-compute checksums ONCE (was previously recomputed per candidate)
    cached_crc32 = compute_crc32(data)
    cached_sha256 = compute_sha256(data)

    # Pre-compute the filename bytes length (constant across candidates)
    name_bytes_len = len(Path(original_filename).name.encode('utf-8'))

    best_transform: BaseTransform | None = None
    best_codec: BaseCodec | None = None
    best_size = float('inf')
    best_meta: bytes | None = None
    best_payload: bytes | None = None

    store_transform: BaseTransform | None = None
    store_codec: BaseCodec | None = None
    store_size = float('inf')
    store_meta: bytes | None = None
    store_payload: bytes | None = None

    for transform, codec in candidates:
        try:
            # 1. Apply transform
            trans_meta, transformed_data = transform.transform(data)
            # 2. Apply codec
            codec_meta, payload = codec.compress(transformed_data)
            # 3. Combine metadata
            full_meta = pack_combined_metadata(trans_meta, codec_meta)

            # 4. Compute archive size arithmetically (no allocation)
            arc_size = compute_archive_size(name_bytes_len, len(full_meta), len(payload))

            label = codec.__class__.__name__.replace('Codec', '')
            if transform.transform_id != 0:
                label = f"{transform.name} + {label}"

            evaluations.append(CandidateEvaluation(
                transform_name=transform.name,
                codec_name=codec.__class__.__name__.replace('Codec', ''),
                display_label=label,
                archive_size=arc_size
            ))

            if isinstance(transform, IdentityTransform) and isinstance(codec, StoreCodec):
                store_transform = transform
                store_codec = codec
                store_size = arc_size
                store_meta = full_meta
                store_payload = payload

            # Deterministic tie-breaking: strictly smaller size wins
            if arc_size < best_size:
                best_size = arc_size
                best_transform = transform
                best_codec = codec
                best_meta = full_meta
                best_payload = payload

        except Exception:
            # Skip invalid/failing candidate
            continue

    # Fallback to STORE if no compressed archive is strictly smaller than STORE
    if best_transform is None or best_size >= store_size:
        best_transform = store_transform
        best_codec = store_codec
        best_size = store_size
        best_meta = store_meta
        best_payload = store_payload

    # Only serialize the WINNER (was previously serialized for every candidate)
    best_bytes = serialize_archive(
        filename=original_filename,
        original_data=data,
        profile_id=profile_id,
        transform_id=best_transform.transform_id,
        codec_id=best_codec.algorithm_id,
        codec_level=0,
        transform_meta=best_meta,
        payload=best_payload,
        precomputed_crc32=cached_crc32,
        precomputed_sha256=cached_sha256
    )

    # Mark winner in evaluations list
    best_label = best_codec.__class__.__name__.replace('Codec', '')
    if best_transform.transform_id != 0:
        best_label = f"{best_transform.name} + {best_label}"

    for ev in evaluations:
        if ev.display_label == best_label:
            ev.is_winner = True
            break

    return CandidateSelectionResult(
        best_archive_bytes=best_bytes,
        best_transform=best_transform,
        best_codec=best_codec,
        best_size=best_size,
        evaluations=evaluations
    )
