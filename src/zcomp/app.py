import sys
from pathlib import Path
from .file_dialog import select_file
from .filesystem import get_downloads_path, get_safe_output_path
from .archive import create_archive, extract_archive
from .errors import ArchiveValidationError
from .metrics import Timer, format_size
from .profiles import Profile
from .validation import validate_selection, get_profile_name
from .codecs import get_codec

def print_banner():
    print("========================================")
    print("   ZERO-COMPRESS - LOSSLESS FILE TOOL")
    print("========================================")

def select_profile() -> int:
    print("\nSelect the type of file you want to compress:")
    print("1. Text (.txt)")
    print("2. PDF (.pdf)")
    print("3. PNG (.png)")
    print("4. JPEG (.jpg/.jpeg)")
    print("5. MP4 (.mp4)")
    print("6. Any File Type")
    
    while True:
        choice = input("Select an option [1-6]: ").strip()
        if choice == '1': return Profile.TXT
        if choice == '2': return Profile.PDF
        if choice == '3': return Profile.PNG
        if choice == '4': return Profile.JPEG
        if choice == '5': return Profile.MP4
        if choice == '6': return Profile.ANY
        print("Invalid selection.")

def compress_flow():
    print("\n[Compress Mode]")
    profile_id = select_profile()
    
    while True:
        filepath = select_file("compress", profile_id)
        if not filepath:
            print("Operation cancelled.")
            return

        if validate_selection(filepath, profile_id):
            break
            
        print("\nInvalid file type.")
        print(f"Expected: {get_profile_name(profile_id)}")
        print(f"Selected: {filepath.name}")
        retry = input("Select another file? [Y/N]: ").strip().lower()
        if retry != 'y':
            return

    print(f"\nSelected file: {filepath.name}")
    
    try:
        with open(filepath, 'rb') as f:
            data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
        
    print("Compressing... (Please wait)")
    timer = Timer()
    timer.start()
    
    try:
        archive_bytes, algorithm_id = create_archive(filepath, data, profile_id)
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
    
    alg_name = get_codec(algorithm_id).__class__.__name__.replace('Codec', '')
    if alg_name == 'Store':
        alg_name = 'STORE (No gains found)'
    
    print("\n--- Success ---")
    print(f"Algorithm Used:   {alg_name}")
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

        if filepath.suffix.lower() == '.zc':
            break
            
        print("\nInvalid file type.")
        print("Please select a .zc archive.")
        retry = input("Select another file? [Y/N]: ").strip().lower()
        if retry != 'y':
            return

    print(f"Selected archive: {filepath.name}")
    
    try:
        with open(filepath, 'rb') as f:
            archive_data = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return
        
    print("Decompressing... (Please wait)")
    timer = Timer()
    timer.start()
    
    try:
        orig_name, decoded_data, alg_id = extract_archive(archive_data)
    except ArchiveValidationError as e:
        print(f"\nERROR: {e}")
        return
    except Exception as e:
        print(f"\nDecompression failed: {e}")
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
        
    alg_name = get_codec(alg_id).__class__.__name__.replace('Codec', '')
    if alg_name == 'Store': alg_name = 'STORE'
    
    print("\n--- Success ---")
    print(f"Algorithm Used:   {alg_name}")
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
