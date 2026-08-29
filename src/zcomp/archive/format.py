import struct
from pathlib import Path
from ..errors import ArchiveValidationError
from ..verification import compute_crc32, compute_sha256

MAGIC = b"ZCMP"
VERSION = 3

# MAGIC(4), VERSION(2), FLAGS(1), PROFILE_ID(1), TRANSFORM_ID(1), CODEC_ID(1), CODEC_LEVEL(1),
# ORIG_SIZE(8), PAYLOAD_SIZE(8), CRC32(4), SHA256(32), NAME_LEN(2)
HEADER_STRUCT = "!4s H B B B B B Q Q I 32s H"
HEADER_SIZE = struct.calcsize(HEADER_STRUCT)

class ArchiveHeader:
    def __init__(
        self,
        magic: bytes,
        version: int,
        flags: int,
        profile_id: int,
        transform_id: int,
        codec_id: int,
        codec_level: int,
        orig_size: int,
        payload_size: int,
        crc32: int,
        sha256: bytes,
        filename: str,
        transform_meta: bytes
    ):
        self.magic = magic
        self.version = version
        self.flags = flags
        self.profile_id = profile_id
        self.transform_id = transform_id
        self.codec_id = codec_id
        self.codec_level = codec_level
        self.orig_size = orig_size
        self.payload_size = payload_size
        self.crc32 = crc32
        self.sha256 = sha256
        self.filename = filename
        self.transform_meta = transform_meta

def serialize_archive(
    filename: str,
    original_data: bytes,
    profile_id: int,
    transform_id: int,
    codec_id: int,
    codec_level: int,
    transform_meta: bytes,
    payload: bytes
) -> bytes:
    """Serializes file data and metadata into complete .ZC archive bytes."""
    orig_size = len(original_data)
    payload_size = len(payload)
    crc32_val = compute_crc32(original_data)
    sha256_val = compute_sha256(original_data)
    
    name_bytes = Path(filename).name.encode('utf-8')
    name_len = len(name_bytes)
    flags = 0

    header_bytes = struct.pack(
        HEADER_STRUCT,
        MAGIC,
        VERSION,
        flags,
        profile_id,
        transform_id,
        codec_id,
        codec_level,
        orig_size,
        payload_size,
        crc32_val,
        sha256_val,
        name_len
    )

    archive = bytearray(header_bytes)
    archive.extend(name_bytes)
    archive.extend(struct.pack("!I", len(transform_meta)))
    archive.extend(transform_meta)
    archive.extend(payload)

    return bytes(archive)

def deserialize_archive(archive_data: bytes) -> tuple[ArchiveHeader, bytes]:
    """
    Deserializes a .ZC archive.
    Returns (ArchiveHeader, payload_bytes).
    """
    if len(archive_data) < HEADER_SIZE:
        raise ArchiveValidationError("Archive is too small (truncated header)")

    (
        magic,
        version,
        flags,
        profile_id,
        transform_id,
        codec_id,
        codec_level,
        orig_size,
        payload_size,
        crc32_val,
        sha256_val,
        name_len
    ) = struct.unpack(HEADER_STRUCT, archive_data[:HEADER_SIZE])

    if magic != MAGIC:
        raise ArchiveValidationError("Invalid ZeroShrink archive (magic mismatch).")
    if version not in (2, 3):
        raise ArchiveValidationError(f"Unsupported archive version: {version}")

    offset = HEADER_SIZE

    if len(archive_data) < offset + name_len:
        raise ArchiveValidationError("Unexpected end of archive (filename missing).")

    filename = archive_data[offset : offset + name_len].decode('utf-8', errors='replace')
    offset += name_len

    if len(archive_data) < offset + 4:
        raise ArchiveValidationError("Unexpected end of archive (transform metadata size missing).")

    meta_size = struct.unpack("!I", archive_data[offset : offset + 4])[0]
    offset += 4

    if len(archive_data) < offset + meta_size:
        raise ArchiveValidationError("Invalid transform metadata boundaries.")

    transform_meta = archive_data[offset : offset + meta_size]
    offset += meta_size

    if len(archive_data) < offset + payload_size:
        raise ArchiveValidationError("Invalid payload boundaries (truncated payload).")

    payload = archive_data[offset : offset + payload_size]

    header = ArchiveHeader(
        magic=magic,
        version=version,
        flags=flags,
        profile_id=profile_id,
        transform_id=transform_id,
        codec_id=codec_id,
        codec_level=codec_level,
        orig_size=orig_size,
        payload_size=payload_size,
        crc32=crc32_val,
        sha256=sha256_val,
        filename=filename,
        transform_meta=transform_meta
    )

    return header, payload
