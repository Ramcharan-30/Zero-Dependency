import sys
from pathlib import Path
from .file_dialog import select_file
from .filesystem import get_downloads_path, get_safe_output_path
from .archive import create_archive, extract_archive, ALG_HUFFMAN, ALG_RLE
from .errors import ArchiveValidationError
from .metrics import Timer, format_size

def print_banner():
    print("========================================")
    print("   ZERO-COMPRESS - LOSSLESS FILE TOOL")
    print("========================================")

def compress_flow():
    print("\n[Compress Mode]")
    filepath = select_file("compress")
    if not filepath:
        print("Operation cancelled.")
        return

    print(f"Selected file: {filepath.name}")
    
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
        
    print("Select compression method:")
    print("1. Huffman (Default)")
    print("2. RLE")
    choice = input("Select [1/2]: ").strip()
    
    algorithm = ALG_RLE if choice == '2' else ALG_HUFFMAN
        
    timer = Timer()
    timer.start()
    
    try:
        archive_bytes = create_archive(filepath, data, algorithm=algorithm)
    except Exception as e:
        print(f"Compression failed: {e}")
        return
        
    timer.stop()
    
    downloads_dir = get_downloads_path()
    output_filename = filepath.with_suffix('.zc').name
    out_path = get_safe_output_path(downloads_dir, output_filename)
    
    try:
        with open(out_path, 'wb') as f:
            f.write(archive_bytes)
    except Exception as e:
        print(f"Error writing archive: {e}")
        return
        
    orig_size = len(data)
    comp_size = len(archive_bytes)
    ratio = (comp_size / orig_size * 100) if orig_size > 0 else 100
    
    print("\n--- Success ---")
    print(f"Original size:    {format_size(orig_size)}")
    print(f"Archive size:     {format_size(comp_size)}")
    print(f"Ratio:            {ratio:.2f}%")
    print(f"Time taken:       {timer.elapsed:.4f}s")
    print(f"Output saved to:  {out_path}")

def decompress_flow():
    print("\n[Decompress Mode]")
    while True:
        filepath = select_file("decompress")
        if not filepath:
            print("Operation cancelled.")
            return

        print(f"Selected archive: {filepath.name}")
        
        try:
            with open(filepath, 'rb') as f:
                archive_data = f.read()
        except Exception as e:
            print(f"Error reading file: {e}")
            return
            
        timer = Timer()
        timer.start()
        
        try:
            orig_name, decoded_data = extract_archive(archive_data)
            break
        except ArchiveValidationError as e:
            print(f"ERROR: {e}")
            retry = input("Select another file? [Y/N]: ").strip().lower()
            if retry != 'y':
                return
        except Exception as e:
            print(f"Decompression failed: {e}")
            return
            
    timer.stop()
    
    downloads_dir = get_downloads_path()
    out_path = get_safe_output_path(downloads_dir, orig_name)
    
    try:
        with open(out_path, 'wb') as f:
            f.write(decoded_data)
    except Exception as e:
        print(f"Error writing extracted file: {e}")
        return
        
    print("\n--- Success ---")
    print(f"Restored size:    {format_size(len(decoded_data))}")
    print(f"Time taken:       {timer.elapsed:.4f}s")
    print(f"Output saved to:  {out_path}")

def run():
    print_banner()
    while True:
        print("\nWhat would you like to do?")
        print("1. Compress a file")
        print("2. Decompress a .zc file")
        print("3. Exit")
        
        choice = input("\nSelect an option: ").strip()
        
        if choice == '1':
            compress_flow()
        elif choice == '2':
            decompress_flow()
        elif choice == '3':
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection. Please enter 1, 2, or 3.")
