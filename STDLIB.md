# STDLIB Log - ZeroShrink

This document logs the substitutions made to ensure ZeroShrink has zero third-party dependencies.

| Normal Package | Stdlib / Custom Substitution | Rationale |
| :--- | :--- | :--- |
| `zstd` / `lz4` | `zlib`, `lzma`, `bz2` | Used built-in Python compression modules instead of external C-extensions. |
| `bitstring` | Integer Bit-Buffer & Bit-Shifting | Native bitwise shift arithmetic (`<<`, `>>`, `|`) and bit masks for ultra-fast custom Huffman implementation. |
| `PriorityQueue` | `heapq` | Used `heapq` for O(log n) tree construction in Huffman coding. |
| `Pandas` / `Numpy` | `collections.Counter` | Frequency analysis handled by the standard library Counter. |
| `PyQt` / `Kivy` | `tkinter` / `ttk` | Native GUI toolkit with `ttk.Progressbar` and multi-threaded event handlers to eliminate massive binary dependencies. |
| `celery` / `threading` | `threading.Thread` | Native Python daemon threads for non-blocking file compression and extraction operations. |
| `PyYAML` / `json` | `pickle` + `json` | Binary serialization for Huffman metadata and history tracking via standard `json`. |
| `argparse` | `sys.argv` | Direct system argument access for lightweight CLI interactions. |
| `hashlib` / `crc32` | `zlib.crc32` / `hashlib` | Used stdlib CRC32 and SHA-256 for archive integrity verification. |
| `pathlib` | `os.path` | Fundamental OS primitives for cross-platform compatibility. |
