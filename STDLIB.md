# Standard Library Explanations

This document explicitly lists the Python Standard Library components we used as substitutes for common third-party dependencies, as part of our adherence to the zero-dependency requirements.

- **CLI framework** -> `argparse` / `input()`
    - **Why**: The standard library is completely sufficient for this application's simple interactive command flow.
- **GUI file picker** -> `tkinter` / `tkinter.filedialog`
    - **Why**: Gives a native file-selection dialog without requiring heavy external dependencies like PyQt or Tkinter wrappers.
- **Binary packing** -> `struct`
    - **Why**: Allows easy translation between Python values and C structs for our custom `.zc` format header.
- **Priority queue** -> `heapq`
    - **Why**: Crucial for optimally building the Huffman tree in $O(N \log N)$ time.
- **Frequency counting** -> `collections.Counter`
    - **Why**: Simplifies calculating byte frequencies across the file.
- **CRC32** -> `zlib.crc32`
    - **Why**: Validates file integrity and ensures corrupted files are caught before decompression completes.
- **Testing** -> `unittest`
    - **Why**: Allows building test suites without using `pytest`.
- **Benchmark timing** -> `time.perf_counter`
    - **Why**: High-resolution clock perfect for tracking compression performance.
- **Filesystem / Paths** -> `pathlib` / `os`
    - **Why**: Used for cross-platform file path resolution, particularly determining the user's Downloads directory.
- **Bit array / Bit manipulations** -> Hand-written `BitWriter` and `BitReader`
    - **Why**: Built-in Python doesn't have an exact equivalent, but we implemented these natively to handle bit-level Huffman streams.
