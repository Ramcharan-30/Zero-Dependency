import struct
import zlib
from pathlib import Path
from . import huffman
from . import rle
from .errors import ArchiveValidationError

MAGIC = b"ZCMP"
VERSION = 1

ALG_HUFFMAN = 1
ALG_RLE = 2

# MAGIC(4), VERSION(2), ALG_ID(2), ORIG_SIZE(8), ORIG_CRC(4), META_SIZE(4), NAME_LEN(2)
HEADER_STRUCT = "!4s H H Q I I H"
HEADER_SIZE = struct.calcsize(HEADER_STRUCT)

def create_archive(original_path: Path, data: bytes, algorithm: int = ALG_HUFFMAN) -> bytes:
    orig_size = len(data)
    orig_crc = zlib.crc32(data) & 0xFFFFFFFF
    
    name_bytes = original_path.name.encode('utf-8')
    name_len = len(name_bytes)
    
    if algorithm == ALG_HUFFMAN:
        meta, payload = huffman.compress(data)
    elif algorithm == ALG_RLE:
        meta, payload = rle.compress(data)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
        
    meta_size = len(meta)
    
    header = struct.pack(
        HEADER_STRUCT,
        MAGIC,
        VERSION,
        algorithm,
        orig_size,
        orig_crc,
        meta_size,
        name_len
    )
    
    return header + name_bytes + meta + payload

def extract_archive(archive_data: bytes) -> tuple[str, bytes]:
    if len(archive_data) < HEADER_SIZE:
        raise ArchiveValidationError("Archive is too small (truncated header)")
        
    header_bytes = archive_data[:HEADER_SIZE]
    magic, version, alg_id, orig_size, orig_crc, meta_size, name_len = struct.unpack(HEADER_STRUCT, header_bytes)
    
    if magic != MAGIC:
        raise ArchiveValidationError("Invalid Zero-Compress magic signature")
    if version != VERSION:
        raise ArchiveValidationError(f"Unsupported archive version: {version}")
        
    offset = HEADER_SIZE
    
    if len(archive_data) < offset + name_len:
        raise ArchiveValidationError("Archive is truncated (filename missing)")
        
    name_bytes = archive_data[offset : offset + name_len]
    orig_name = name_bytes.decode('utf-8', errors='replace')
    offset += name_len
    
    if len(archive_data) < offset + meta_size:
        raise ArchiveValidationError("Archive is truncated (metadata missing)")
        
    meta = archive_data[offset : offset + meta_size]
    offset += meta_size
    
    payload = archive_data[offset:]
    
    if alg_id == ALG_HUFFMAN:
        decompressed_data = huffman.decompress(meta, payload)
    elif alg_id == ALG_RLE:
        decompressed_data = rle.decompress(meta, payload)
    else:
        raise ArchiveValidationError(f"Unknown algorithm ID: {alg_id}")
        
    if len(decompressed_data) != orig_size:
        raise ArchiveValidationError(f"Size mismatch: expected {orig_size}, got {len(decompressed_data)}")
        
    actual_crc = zlib.crc32(decompressed_data) & 0xFFFFFFFF
    if actual_crc != orig_crc:
        raise ArchiveValidationError("CRC verification failed (corrupted data)")
        
    return orig_name, decompressed_data
