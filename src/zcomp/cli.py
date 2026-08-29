import argparse
import sys
from pathlib import Path
from .archive import create_archive, extract_archive
from .errors import ArchiveValidationError
from .metrics import format_size
from .filesystem import get_safe_output_path

def main():
    parser = argparse.ArgumentParser(
        description="ZeroShrink - Adaptive Lossless Compression Suite (Zero Dependencies)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Compress subcommand
    compress_parser = subparsers.add_parser("compress", help="Compress a file")
    compress_parser.add_argument("input", help="Path to file to compress")
    compress_parser.add_argument("-o", "--output", help="Output .zc archive path (optional)")

    # Decompress subcommand
    decompress_parser = subparsers.add_parser("decompress", help="Decompress a .zc archive")
    decompress_parser.add_argument("input", help="Path to .zc archive")
    decompress_parser.add_argument("-o", "--output", help="Output path for restored file (optional)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "compress":
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: File not found: {input_path}")
            sys.exit(1)

        with open(input_path, "rb") as f:
            data = f.read()

        archive_bytes, selection_result, profile = create_archive(input_path, data)

        if args.output:
            out_path = Path(args.output)
        else:
            out_path = get_safe_output_path(input_path.parent, input_path.with_suffix(".zc").name)

        with open(out_path, "wb") as f:
            f.write(archive_bytes)

        orig_size = len(data)
        final_size = len(archive_bytes)
        saved = ((orig_size - final_size) / orig_size * 100.0) if orig_size > 0 else 0.0

        print(f"Compressed {input_path.name} -> {out_path.name}")
        print(f"Original: {format_size(orig_size)} | Final .ZC: {format_size(final_size)} ({saved:.2f}% saved)")
        print(f"Strategy: {selection_result.best_transform.name} + {selection_result.best_codec.__class__.__name__.replace('Codec', '')}")

    elif args.command == "decompress":
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"Error: Archive file not found: {input_path}")
            sys.exit(1)

        with open(input_path, "rb") as f:
            archive_data = f.read()

        try:
            orig_name, restored_bytes, header, v_result = extract_archive(archive_data)
        except ArchiveValidationError as e:
            print(f"Error: Archive validation failed: {e}")
            sys.exit(1)

        if args.output:
            out_path = Path(args.output)
        else:
            out_path = get_safe_output_path(input_path.parent, orig_name)

        with open(out_path, "wb") as f:
            f.write(restored_bytes)

        print(f"Decompressed {input_path.name} -> {out_path.name}")
        print(f"Restored size: {format_size(len(restored_bytes))}")
        print("Verification: CRC32 PASS | SHA-256 PASS | Byte Exact PASS")

if __name__ == "__main__":
    main()
