# Zero-Compress (Format-Aware Edition)

A practical desktop-style lossless file compression utility built entirely without third-party dependencies using Python's standard library. 

This project implements format-aware compression strategies that select the optimal algorithm (ZSTD, LZMA, zlib, custom Huffman, custom RLE, or STORE) based on the user's file type, saving it in a custom `.ZC` archive format.

## Features

- **Zero Dependencies**: Pure Python standard library implementation.
- **Format-Aware Strategy**: Dynamically picks the best codec depending on the content (e.g. Text vs PDF vs MP4).
- **Auto Mode Comparison**: For 'Any File Type', compresses using multiple candidate algorithms and selects the smallest valid representation.
- **Custom .ZC Archive Format**: Fully-featured archive format packing magic bytes, file type ID, algorithm ID, CRC32 checks, metadata, and dynamic payload.
- **Corruption Detection**: Built-in CRC32 verification ensures files are strictly checked against corruption on decompression.
- **Interactive UI**: Simple console flow with native `tkinter` GUI file picking. 

## Requirements
- Python 3.10+ (tested up to Python 3.14.7)

## How to Run

1. Clone or download this repository.
2. Ensure you have Python installed. You do **not** need to install any external dependencies.
3. Open a terminal or command prompt and navigate to the project directory:

```bash
cd zero-dep
```

4. Run the application:

```bash
python run.py
```

### Usage Workflow

When you run the application, you will be presented with a menu:

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
2. Select the file profile for your file (TXT, PDF, PNG, JPEG, MP4, or Any File Type).
3. A file selection dialog will open, filtered appropriately. Pick your file.
4. The application automatically determines the best compression algorithm and saves the resulting `.zc` archive in your system's **Downloads** folder.

**Decompressing a File:**
1. Type `2` and press Enter.
2. A file selection dialog will open automatically filtered for `.zc` archives. Pick your compressed file.
3. The application will decode it using the algorithm specified in the archive, verify the CRC32 integrity, and save the original file back to your system's **Downloads** folder.
