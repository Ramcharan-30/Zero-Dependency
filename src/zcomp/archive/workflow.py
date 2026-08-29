from pathlib import Path
from ..errors import ArchiveValidationError
from ..profiler import profile_content, ContentProfile
from ..transforms import get_transform
from ..codecs import get_codec
from ..strategy import (
    select_best_candidate,
    CandidateSelectionResult,
    unpack_combined_metadata
)
from .format import (
    deserialize_archive,
    ArchiveHeader
)
from ..verification import verify_restoration, VerificationResult

def create_archive(
    original_path: Path,
    data: bytes,
    profile_id: int = 255
) -> tuple[bytes, CandidateSelectionResult, ContentProfile]:
    """
    Profiles input file, runs candidate selection across transforms and codecs,
    builds the smallest valid .ZC archive, and returns (archive_bytes, selection_result, content_profile).
    """
    profile = profile_content(data, ext_hint=original_path.suffix)
    selection_result = select_best_candidate(
        original_filename=original_path.name,
        data=data,
        profile=profile,
        profile_id=profile_id
    )
    return selection_result.best_archive_bytes, selection_result, profile

def extract_archive(archive_data: bytes) -> tuple[str, bytes, ArchiveHeader, VerificationResult]:
    """
    Extracts and verifies a .ZC archive.
    Returns (original_filename, decompressed_bytes, header, verification_result).
    Raises ArchiveValidationError if validation or checksum checks fail.
    """
    header, payload = deserialize_archive(archive_data)

    trans_meta, codec_meta = unpack_combined_metadata(header.transform_meta)

    # 1. Resolve Codec and decompress payload
    try:
        codec = get_codec(header.codec_id)
        transformed_data = codec.decompress(codec_meta, payload)
    except Exception as e:
        raise ArchiveValidationError(f"Codec decompression failed: {e}")

    # 2. Resolve Transform and inverse transform
    try:
        transform = get_transform(header.transform_id)
        restored_data = transform.inverse(trans_meta, transformed_data)
    except Exception as e:
        raise ArchiveValidationError(f"Transform inverse operation failed: {e}")

    # 3. Dual integrity verification (CRC32 + SHA-256 + Original Size)
    result = verify_restoration(
        restored_data=restored_data,
        expected_size=header.orig_size,
        expected_crc32=header.crc32,
        expected_sha256=header.sha256
    )

    if not result.is_valid:
        raise ArchiveValidationError(result.error_message)

    return header.filename, restored_data, header, result
