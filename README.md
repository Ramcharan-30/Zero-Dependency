# ZeroShrink - Adaptive Lossless Compression Suite

> **Zero Dependency Hackathon 2026 Submission** | Track F - Open / Wildcard

ZeroShrink is an adaptive lossless file compression engine built **100% with the Python Standard Library** without any third-party runtime dependencies.

Instead of relying on rigid file extensions, ZeroShrink profiles the actual byte structure of a file, evaluates candidate combinations of **reversible pre-processing transforms** (Delta, RLE, Byte Shuffle) and **codecs** (STORE, ZSTD, LZMA, BZ2, ZLIB, Huffman, RLE), serializes full `.ZC` archives, and selects the **smallest valid representation** with dual CRC32 + SHA-256 integrity verification.

---

## Key Features

- **Zero Third-Party Dependencies**: Built purely on Python stdlib. `requirements.txt` is empty.
- **Content-Aware Byte Profiler**: Measures Shannon entropy, byte diversity, printable ratios, consecutive run potential, token repetition, and magic signatures (PNG, PDF, JPEG, MP4, GZIP, ZIP, XZ, ZSTD, BZ2).
- **Reversible Pre-processing Transforms**:
  - `DELTA8`: 8-bit modular difference transform to expose patterns in structured numeric data.
  - `RLE_TRANSFORM`: Run-length encoding preprocessing to compress repetitive byte streams.
  - `SHUFFLE32` / `SHUFFLE64`: Byte-plane shuffling for 32-bit and 64-bit binary record structures.
- **Adaptive Candidate Selection**: Evaluates candidates against complete `.ZC` serialization size. Winners are selected based on actual final archive size rather than raw payload size.
- **Dual Checksum Integrity & Corruption Protection**: Validates size, CRC32, and SHA-256 digest on extraction. Rejects corrupted archives prior to writing output files.
- **Interactive Console UI & CLI**: Supports interactive UI with Tkinter native file picking as well as command-line execution (`python -m src.zcomp.cli`).

---

## How to Run

### Interactive Application
```bash
python run.py
```

### CLI Command
```bash
# Compress a file
python -m src.zcomp.cli compress path/to/file.bin -o output.zc

# Decompress an archive
python -m src.zcomp.cli decompress path/to/output.zc -o restored.bin
```

### Run Test Suite
```bash
python -m unittest discover tests
```

### Run Benchmarks
```bash
python benchmarks/benchmark.py
```

---

## Archive (.ZC) Layout

```text
+-------------------------------------------------------------+
| MAGIC (b"ZCMP", 4B) | VERSION (uint16, 2B) | FLAGS (uint8)   |
| PROFILE_ID (uint8) | TRANSFORM_ID (uint8) | CODEC_ID (uint8) |
| CODEC_LEVEL (uint8)| ORIGINAL_SIZE (uint64)| PAYLOAD_SIZE    |
| CRC32 (uint32)     | SHA256 (32B raw)     | FILENAME_LEN    |
+-------------------------------------------------------------+
| FILENAME (UTF-8)   | METADATA_LEN (uint32)| TRANSFORM_META  |
+-------------------------------------------------------------+
| COMPRESSED PAYLOAD BYTES                                    |
+-------------------------------------------------------------+
```

---

## Project Structure

```text
Zero-Dependency/
├── src/
│   └── zcomp/
│       ├── profiler/       # Entropy, statistics, signatures, profiler
│       ├── transforms/     # Identity, Delta8, RLE_Transform, Shuffle32/64
│       ├── codecs/         # Store, Huffman, Rle, Zlib, Lzma, Zstd, Bz2
│       ├── strategy/       # Candidate generator, archive size selector
│       ├── archive/        # Custom .ZC format serializer/deserializer
│       ├── verification/   # CRC32 + SHA-256 integrity verification
│       ├── app.py          # Interactive result UI
│       └── cli.py          # Command-line interface
├── tests/                  # 27 automated unit tests
├── benchmarks/             # Performance benchmark matrix
├── README.md               # Overview documentation
├── STDLIB.md               # Standard library substitution audit
├── deps-proof.txt          # Zero-dependency verification proof
├── requirements.txt        # Empty dependency manifest
└── run.py                  # One-command runnable entrypoint
```
