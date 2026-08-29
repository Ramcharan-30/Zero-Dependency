# Zero-Compress

A practical desktop-style lossless file compression utility built entirely without third-party dependencies using Python's standard library. 

This project implements standard compression algorithms like Huffman Coding and Run-Length Encoding (RLE) to create a custom binary `.ZC` archive format. 

## Features

- **Zero Dependencies**: Pure Python standard library implementation.
- **Huffman & RLE Compression**: Custom-built encoders and decoders.
- **Custom .ZC Archive Format**: Fully-featured archive format packing magic bytes, algorithm ID, CRC32 checks, metadata, and bit-level payload.
- **Corruption Detection**: Built-in CRC32 verification ensures files are strictly checked against corruption on decompression.
- **Interactive UI**: Simple console flow with native `tkinter` GUI file picking. 

## Requirements
- Python 3.10+ (tested up to Python 3.14.7)

## How to Run

1. Clone or download this repository.
2. Ensure you have Python installed. You do **not** need to install any external dependencies (e.g. no `pip install` required).
3. Open a terminal or command prompt and navigate to the project directory:

```bash
cd zero-dep
```

4. Run the application:

```bash
python run.py
```

### Usage Workflow

When you run the application, you will be presented with a simple menu:

```text
========================================
   ZERO-COMPRESS - LOSSLESS FILE TOOL
========================================

What would you like to do?

1. Compress a file
2. Decompress a .zc file
3. Exit
```

**Compressing a File:**
1. Type `1` and press Enter.
2. A file selection dialog will open. Pick any file on your computer (e.g., a `.txt` file, an image, or a binary).
3. You will be prompted to choose a compression algorithm:
   - Type `1` for Huffman (default).
   - Type `2` for Run-Length Encoding (RLE).
4. The file will be compressed into a `.zc` archive and safely stored in your system's **Downloads** folder.

**Decompressing a File:**
1. Type `2` and press Enter.
2. A file selection dialog will open automatically filtered for `.zc` archives. Pick your compressed file.
3. The application will decompress it, verify the CRC32 integrity to ensure no data loss, and save the original file back to your system's **Downloads** folder.
