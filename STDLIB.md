# Standard Library Explanations & Zero-Dependency Substitutions

This document explicitly lists the Python Standard Library components used as substitutes for common third-party dependencies for the **Zero Dependency Hackathon 2026**.

## Substitutions & Mappings

- **CLI framework (`click` / `typer`)** -> `argparse` / `input()`
    - **Why**: The standard library `argparse` and interactive console menu flow are completely sufficient for file processing commands.
- **GUI file picker (`PyQt` / `wxPython`)** -> `tkinter` / `tkinter.filedialog`
    - **Why**: Native desktop file-selection dialog without third-party GUI dependencies.
- **Binary Packing (`ctypes` / C-extension)** -> `struct`
    - **Why**: Translates Python values to C-style struct binary representations for `.ZC` archive headers.
- **Priority Queue & Trees (`networkx` / `pyhuffman`)** -> `heapq`
    - **Why**: Enables building custom Huffman trees in $O(N \log N)$ time using standard library heaps.
- **Frequency Analysis & Profiling (`numpy` / `scipy`)** -> `collections.Counter`, `math`
    - **Why**: Computes exact byte counts, byte diversity, printable ratios, and Shannon entropy $H = -\sum p_i \log_2(p_i)$ without heavy numeric dependencies.
- **Checksums & Integrity Verification (`xxhash` / `pycryptodome`)** -> `zlib.crc32`, `hashlib.sha256`
    - **Why**: Provides fast CRC32 corruption detection and cryptographic SHA-256 byte-for-byte restoration verification.
- **Standard Codecs (`python-zstandard` / `pylzma`)** -> `zlib`, `bz2`, `lzma`, `compression.zstd`
    - **Why**: Leverages Python standard library compression modules directly.
- **File Type & Signature Detection (`python-magic` / `filetype`)** -> Pure stdlib header signature inspector
    - **Why**: Custom lightweight signature parser matching magic bytes for PNG, PDF, JPEG, MP4, GZIP, ZIP, XZ, ZSTD, and BZ2.
- **Testing Framework (`pytest`)** -> `unittest`
    - **Why**: Pure stdlib test runner for automated unit tests.
- **Benchmark Timing (`tqdm` / `benchmark`)** -> `time.perf_counter`
    - **Why**: High-resolution performance timer for compression benchmarks.

---

**Note:** All reversible pre-processing transforms (Identity, Delta8, RLE Transform, Shuffle32, Shuffle64), the custom Huffman and RLE encoders, and the `.ZC` custom archive format were designed and implemented 100% from scratch.
