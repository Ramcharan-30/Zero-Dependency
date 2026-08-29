import struct
from dataclasses import dataclass
from ..profiler import ContentProfile
from ..transforms import BaseTransform, IdentityTransform
from ..codecs import BaseCodec, StoreCodec
from ..archive import serialize_archive
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
    Evaluates candidate (Transform, Codec) pairs by building complete .ZC archives and measuring final sizes.
    Selects the candidate that produces the SMALLEST VALID COMPLETE .ZC ARCHIVE.
    If no candidate reduces archive size compared to STORE, STORE is selected.
    """
    candidates = generate_candidates(profile)
    evaluations: list[CandidateEvaluation] = []
    
    best_bytes: bytes | None = None
    best_transform: BaseTransform | None = None
    best_codec: BaseCodec | None = None
    best_size = float('inf')

    store_bytes: bytes | None = None
    store_transform: BaseTransform | None = None
    store_codec: BaseCodec | None = None
    store_size = float('inf')

    for transform, codec in candidates:
        try:
            # 1. Apply transform
            trans_meta, transformed_data = transform.transform(data)
            # 2. Apply codec
            codec_meta, payload = codec.compress(transformed_data)
            # 3. Combine metadata
            full_meta = pack_combined_metadata(trans_meta, codec_meta)
            
            # 4. Build complete .ZC serialization
            archive_bytes = serialize_archive(
                filename=original_filename,
                original_data=data,
                profile_id=profile_id,
                transform_id=transform.transform_id,
                codec_id=codec.algorithm_id,
                codec_level=0,
                transform_meta=full_meta,
                payload=payload
            )
            
            arc_size = len(archive_bytes)
            
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
                store_bytes = archive_bytes
                store_transform = transform
                store_codec = codec
                store_size = arc_size

            # Deterministic tie-breaking: strictly smaller size wins
            if arc_size < best_size:
                best_size = arc_size
                best_bytes = archive_bytes
                best_transform = transform
                best_codec = codec

        except Exception:
            # Skip invalid/failing candidate
            continue

    # Fallback to STORE if no compressed archive is strictly smaller than STORE
    if best_bytes is None or best_size >= store_size:
        best_bytes = store_bytes
        best_transform = store_transform
        best_codec = store_codec
        best_size = store_size

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
