# ZeroShrink - Lossless Studio

ZeroShrink is a zero-dependency, adaptive lossless file compression engine built for the Zero-Dependency Hackathon. It eliminates all third-party dependencies by reimplementing key compression logic and utilizing only the Python Standard Library.

## 🚀 Features
- **Adaptive Strategy Sampling**: Automatically tests combinations of transforms (Delta8) and codecs (Huffman, Zlib, LZMA, BZ2) using smart 128KB chunk sampling on large files for high-speed candidate selection.
- **Optimized Huffman Engine**: Ultra-fast pure-Python Huffman coding built from scratch using integer bit-buffer manipulation and trie-based prefix decoding.
- **Multi-Threaded GUI with Progress Indicator**: Non-blocking Tkinter studio with background thread workers and real-time loading/progress feedback.
- **Archive Integrity**: Built-in CRC32 checksum verification to detect file corruption on extract.
- **Single File Architecture**: Entire logic (Algorithm + GUI + Strategy) is contained in `zero_shrink.py`.
- **Zero Dependencies**: No `pip install` required.

## 🛠️ How to Run
```bash
python3 zero_shrink.py
```

## 🧪 Testing & Building
- **Run Tests**: `python3 -m unittest tests/test_zero_shrink.py`
- **Reproducible Build**: `python3 build.py`

## ⚠️ Limits
- Pure Python implementation: Re-implemented algorithms run in native Python runtime.
