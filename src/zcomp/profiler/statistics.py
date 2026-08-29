# Pre-computed frozenset of printable ASCII byte values (tab, newline, CR, 0x20..0x7E)
_PRINTABLE_BYTES = frozenset({9, 10, 13} | set(range(32, 127)))

def calculate_byte_diversity(data: bytes) -> float:
    """Returns ratio of unique bytes in sample relative to 256 (0.0 to 1.0)."""
    if not data:
        return 0.0
    return len(set(data)) / 256.0

def calculate_printable_ratio(data: bytes) -> float:
    """Returns ratio of printable ASCII bytes (tab, newline, CR, 0x20..0x7E) to total bytes."""
    if not data:
        return 0.0
    printable = _PRINTABLE_BYTES
    printable_count = sum(1 for b in data if b in printable)
    return printable_count / len(data)

def calculate_run_ratio(data: bytes) -> float:
    """Returns ratio of bytes that belong to consecutive duplicate byte runs."""
    if len(data) <= 1:
        return 0.0
    run_bytes = 0
    in_run = False
    prev = data[0]
    for i in range(1, len(data)):
        curr = data[i]
        if curr == prev:
            run_bytes += 1
            if not in_run:
                run_bytes += 1
                in_run = True
        else:
            in_run = False
        prev = curr
    return run_bytes / len(data)

def calculate_repetition_score(data: bytes) -> float:
    """
    Estimates short n-gram token repetitions (e.g. 4-byte n-grams).
    Returns ratio of duplicate 4-byte windows to total 4-byte windows.
    Uses int-based hashing for faster set operations.
    """
    if len(data) < 8:
        return 0.0
    window_size = 4
    total_windows = len(data) - window_size + 1
    seen = set()
    duplicates = 0
    # Convert 4-byte windows to ints for faster hashing and comparison
    mv = memoryview(data)
    for i in range(total_windows):
        key = int.from_bytes(mv[i:i + window_size], 'big')
        if key in seen:
            duplicates += 1
        else:
            seen.add(key)
    return duplicates / total_windows
