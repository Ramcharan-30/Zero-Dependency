from dataclasses import dataclass
from pathlib import Path
from .entropy import calculate_entropy
from .statistics import (
    calculate_byte_diversity,
    calculate_printable_ratio,
    calculate_run_ratio,
    calculate_repetition_score
)
from .signatures import detect_signature, is_already_compressed

MAX_SAMPLE_SIZE = 64 * 1024  # 64 KB bounded profiling buffer

@dataclass
class ContentProfile:
    file_size: int
    extension: str
    signature: str | None
    entropy: float
    byte_diversity: float
    printable_ratio: float
    run_ratio: float
    repetition_score: float
    is_text: bool
    is_repetitive: bool
    is_structured_binary: bool
    already_compressed: bool
    high_entropy: bool

def get_bounded_sample(data_or_path: bytes | Path | str) -> tuple[int, bytes, str]:
    """
    Extracts a bounded profiling sample from bytes or file path.
    For large files, takes head, middle, and tail samples up to MAX_SAMPLE_SIZE total.
    Returns (file_size, sample_bytes, extension).
    """
    if isinstance(data_or_path, (bytes, bytearray)):
        data = bytes(data_or_path)
        size = len(data)
        if size <= MAX_SAMPLE_SIZE:
            return size, data, ""
        # Head, middle, tail
        chunk_size = MAX_SAMPLE_SIZE // 3
        mid_start = (size - chunk_size) // 2
        sample = data[:chunk_size] + data[mid_start:mid_start + chunk_size] + data[-chunk_size:]
        return size, sample, ""

    path = Path(data_or_path)
    size = path.stat().st_size
    ext = path.suffix.lower()

    if size <= MAX_SAMPLE_SIZE:
        with open(path, "rb") as f:
            return size, f.read(), ext

    chunk_size = MAX_SAMPLE_SIZE // 3
    with open(path, "rb") as f:
        head = f.read(chunk_size)
        f.seek((size - chunk_size) // 2)
        mid = f.read(chunk_size)
        f.seek(size - chunk_size)
        tail = f.read(chunk_size)
        return size, head + mid + tail, ext

def profile_content(data_or_path: bytes | Path | str, ext_hint: str = "") -> ContentProfile:
    """
    Profiles the actual byte structure of a file or byte stream.
    Returns a ContentProfile containing statistical heuristics.
    """
    file_size, sample, ext = get_bounded_sample(data_or_path)
    if not ext and ext_hint:
        ext = ext_hint

    entropy = calculate_entropy(sample)
    diversity = calculate_byte_diversity(sample)
    printable = calculate_printable_ratio(sample)
    run_ratio = calculate_run_ratio(sample)
    repetition = calculate_repetition_score(sample)
    signature = detect_signature(sample)

    already_comp = is_already_compressed(signature, ext)
    high_entropy = entropy > 7.2
    is_text = printable >= 0.85 and entropy < 6.5
    is_repetitive = run_ratio >= 0.15 or repetition >= 0.25
    is_structured_binary = not is_text and not already_comp and entropy < 7.0 and (diversity < 0.6 or repetition > 0.1)

    return ContentProfile(
        file_size=file_size,
        extension=ext,
        signature=signature,
        entropy=entropy,
        byte_diversity=diversity,
        printable_ratio=printable,
        run_ratio=run_ratio,
        repetition_score=repetition,
        is_text=is_text,
        is_repetitive=is_repetitive,
        is_structured_binary=is_structured_binary,
        already_compressed=already_comp,
        high_entropy=high_entropy
    )
