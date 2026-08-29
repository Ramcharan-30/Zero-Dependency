def detect_signature(data: bytes) -> str | None:
    """
    Detects standard binary/container file signature from leading sample bytes.
    Returns format name string if detected, otherwise None.
    """
    if len(data) >= 8 and data[:8] == b"\x89PNG\r\n\x1a\n":
        return "PNG"
    if len(data) >= 4 and data[:4] == b"%PDF":
        return "PDF"
    if len(data) >= 3 and data[:3] == b"\xFF\xD8\xFF":
        return "JPEG"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "MP4"
    if len(data) >= 2 and data[:2] == b"\x1f\x8b":
        return "GZIP"
    if len(data) >= 4 and data[:4] == b"PK\x03\x04":
        return "ZIP"
    if len(data) >= 6 and data[:6] == b"\xfd7zXZ\x00":
        return "XZ"
    if len(data) >= 4 and data[:4] == b"\x28\xb5\x2f\xfd":
        return "ZSTD"
    if len(data) >= 3 and data[:3] == b"BZh":
        return "BZ2"
    return None

def is_already_compressed(signature: str | None, ext: str) -> bool:
    """Returns True if the signature or file extension indicates pre-compressed content."""
    known_compressed_sigs = {"PNG", "JPEG", "MP4", "GZIP", "ZIP", "XZ", "ZSTD", "BZ2"}
    if signature in known_compressed_sigs:
        return True
    ext_lower = ext.lower().lstrip(".")
    known_compressed_exts = {"png", "jpg", "jpeg", "mp4", "m4v", "mov", "zip", "gz", "tgz", "xz", "7z", "rar", "bz2", "zst"}
    return ext_lower in known_compressed_exts
