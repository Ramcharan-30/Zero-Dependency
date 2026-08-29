import hashlib
import zlib
from dataclasses import dataclass

@dataclass
class VerificationResult:
    size_pass: bool
    crc32_pass: bool
    sha256_pass: bool
    is_valid: bool
    error_message: str | None = None

def compute_crc32(data: bytes) -> int:
    """Computes 32-bit unsigned CRC32 checksum."""
    return zlib.crc32(data) & 0xFFFFFFFF

def compute_sha256(data: bytes) -> bytes:
    """Computes 32-byte raw SHA-256 digest."""
    return hashlib.sha256(data).digest()

def verify_restoration(
    restored_data: bytes,
    expected_size: int,
    expected_crc32: int,
    expected_sha256: bytes
) -> VerificationResult:
    """
    Performs full integrity verification on decompressed data.
    Checks expected size, CRC32, and SHA-256 digest.
    """
    actual_size = len(restored_data)
    size_pass = (actual_size == expected_size)
    if not size_pass:
        return VerificationResult(
            size_pass=False,
            crc32_pass=False,
            sha256_pass=False,
            is_valid=False,
            error_message=f"Decompressed size mismatch: expected {expected_size} bytes, got {actual_size} bytes"
        )

    actual_crc = compute_crc32(restored_data)
    crc32_pass = (actual_crc == expected_crc32)
    if not crc32_pass:
        return VerificationResult(
            size_pass=True,
            crc32_pass=False,
            sha256_pass=False,
            is_valid=False,
            error_message=f"CRC32 verification failed: expected 0x{expected_crc32:08X}, got 0x{actual_crc:08X}"
        )

    actual_sha = compute_sha256(restored_data)
    sha256_pass = (actual_sha == expected_sha256)
    if not sha256_pass:
        return VerificationResult(
            size_pass=True,
            crc32_pass=True,
            sha256_pass=False,
            is_valid=False,
            error_message=f"SHA-256 verification failed: digest mismatch"
        )

    return VerificationResult(
        size_pass=True,
        crc32_pass=True,
        sha256_pass=True,
        is_valid=True
    )
