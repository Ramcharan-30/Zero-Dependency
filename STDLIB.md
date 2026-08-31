# STDLIB Log - ZeroShrink

This document logs the substitutions made to ensure ZeroShrink has zero third-party dependencies.

| Normal Package | Stdlib / Custom Substitution | Rationale |
| :--- | :--- | :--- |
| `zstd` / `lz4` | `zlib`, `lzma`, `bz2` | Used built-in Python compression modules instead of external C-extensions. |
| `bitstring` | `bin()` + `int(x, 2)` | Native bit-manipulation for the custom Huffman implementation. |
| `PriorityQueue` | `heapq` | Used `heapq` for O(log n) tree construction in Huffman coding. |
| `Pandas` / `Numpy` | `collections.Counter` | Frequency analysis handled by the standard library Counter. |
| `PyQt` / `Kivy` | `tkinter` | Native GUI toolkit to eliminate massive binary dependencies. |
| `PyYAML` / `json` | `pickle` | Binary serialization for the Huffman mapping metadata. |
| `argparse` | `sys.argv` | Direct system argument access for lightweight CLI interactions. |
| `hashlib` (ext) | `hashlib` (std) | Used stdlib SHA-256 for integrity verification. |
| `pathlib` (ext) | `os.path` | Stuck to fundamental OS primitives for maximum compatibility. |
| `Loguru` | `sys.stderr` | Standard error streams used for logging to avoid dependency overhead. |
