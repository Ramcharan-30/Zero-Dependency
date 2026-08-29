import struct
import zlib
from pathlib import Path
from .errors import ArchiveValidationError
from .profiles import Profile
from .strategy import select_best_codec
from .codecs import get_codec

MAGIC = b"ZCMP"
VERSION = 2

# MAGIC(4), VERSION(2), FILE_TYPE(1), ALG_ID(1), FLAGS(1), ORIG_SIZE(8), ORIG_CRC(4), NAME_LEN(2)
HEADER_STRUCT = "!4s H B B B Q I H"
HEADER_SIZE = struct.calcsize(HEADER_STRUCT)

def create_archive(original_path: Path, data: bytes, profile_id: int) -> tuple[bytes, int]:
    """Returns (archive_bytes, algorithm_id_used)"""
    orig_size = len(data)
    orig_crc = zlib.crc32(data) & 0xFFFFFFFF
    
    name_bytes = original_path.name.encode('utf-8')
    name_len = len(name_bytes)
    
    best_codec, meta, payload = select_best_codec(data, profile_id)
    algorithm_id = best_codec.algorithm_id
    
    flags = 0
    meta_size = len(meta)
    payload_size = len(payload)
    
    header = struct.pack(
        HEADER_STRUCT,
        MAGIC,
        VERSION,
        profile_id,
        algorithm_id,
        flags,
        orig_size,
        orig_crc,
        name_len
    )
    
    archive = bytearray(header)
    archive.extend(name_bytes)
    archive.extend(struct.pack("!I", meta_size))
    archive.extend(meta)
    archive.extend(struct.pack("!Q", payload_size))
    archive.extend(payload)
    
    return bytes(archive), algorithm_id

def extract_archive(archive_data: bytes) -> tuple[str, bytes, int]:
    """Returns (original_filename, decompressed_data, algorithm_id)"""
    if len(archive_data) < HEADER_SIZE:
        raise ArchiveValidationError("Archive is too small (truncated header)")
        
    header_bytes = archive_data[:HEADER_SIZE]
    magic, version, file_type, alg_id, flags, orig_size, orig_crc, name_len = struct.unpack(HEADER_STRUCT, header_bytes)
    
    if magic != MAGIC:
        raise ArchiveValidationError("Invalid Zero-Compress archive.")
    if version != VERSION:
        raise ArchiveValidationError(f"Unsupported archive version: {version}")
        
    offset = HEADER_SIZE
    
    if len(archive_data) < offset + name_len:
        raise ArchiveValidationError("Unexpected end of archive (filename missing).")
        
    name_bytes = archive_data[offset : offset + name_len]
    orig_name = name_bytes.decode('utf-8', errors='replace')
    offset += name_len
    
    if len(archive_data) < offset + 4:
        raise ArchiveValidationError("Unexpected end of archive (metadata size missing).")
        
    meta_size = struct.unpack("!I", archive_data[offset:offset+4])[0]
    offset += 4
    
    if len(archive_data) < offset + meta_size:
        raise ArchiveValidationError("Invalid metadata boundaries.")
        
    meta = archive_data[offset : offset + meta_size]
    offset += meta_size
    
    if len(archive_data) < offset + 8:
        raise ArchiveValidationError("Unexpected end of archive (payload size missing).")
        
    payload_size = struct.unpack("!Q", archive_data[offset:offset+8])[0]
    offset += 8
    
    if len(archive_data) < offset + payload_size:
        raise ArchiveValidationError("Payload boundaries invalid.")
        
    payload = archive_data[offset : offset + payload_size]
    
    codec = get_codec(alg_id)
    decompressed_data = codec.decompress(meta, payload)
        
    if len(decompressed_data) != orig_size:
        raise ArchiveValidationError(f"Decompressed size mismatch: expected {orig_size}, got {len(decompressed_data)}")
        
    actual_crc = zlib.crc32(decompressed_data) & 0xFFFFFFFF
    if actual_crc != orig_crc:
        raise ArchiveValidationError("CRC verification failed.")
        
    return orig_name, decompressed_data, alg_id
