# ZeroShrink - Lossless Studio

ZeroShrink is a zero-dependency, adaptive lossless file compression engine built for the Zero-Dependency Hackathon. It eliminates all third-party dependencies by reimplementing key compression logic and utilizing only the Python Standard Library.

## 🚀 Features
- **Adaptive Selection**: Automatically tests multiple combinations of transforms (Delta8) and codecs (Huffman, Zlib, LZMA, BZ2) to find the smallest output.
- **Custom Huffman Implementation**: A "Package Killer" reimplementation of Huffman coding from scratch.
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
- Pure Python implementation: Slower than C-based alternatives.
- Memory-bound: Reads files into memory; not suitable for multi-gigabyte files.
