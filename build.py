#!/usr/bin/env python3
"""
Reproducible Build Script for ZeroShrink
Zero Dependency Hackathon 2026 - Track F
"""

import os
import sys
import hashlib
import tarfile
import tempfile
import shutil
import gzip
from datetime import datetime

# Ensure stdout supports UTF-8 on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Constants
PROJECT_NAME = "ZeroShrink"
VERSION = datetime.now().strftime("%Y.%m.%d")
SOURCE_FILES = ["zero_shrink.py", "STDLIB.md"]
OUTPUT_NAME = f"{PROJECT_NAME}-{VERSION}.tar.gz"

def reset_tar_info(tarinfo):
    """Filter function to normalize tar info metadata for reproducibility."""
    tarinfo.mtime = 0
    tarinfo.uid = 0
    tarinfo.gid = 0
    tarinfo.uname = ""
    tarinfo.gname = ""
    return tarinfo

def create_artifact(output_path):
    """Create a deterministic tar.gz artifact with zero embedded timestamps."""
    with open(output_path, "wb") as f_out:
        with gzip.GzipFile(filename="", mode="wb", fileobj=f_out, mtime=0) as gz_out:
            with tarfile.open(fileobj=gz_out, mode="w") as tar:
                for filename in sorted(SOURCE_FILES):
                    if not os.path.exists(filename):
                        raise FileNotFoundError(f"Missing required source file: {filename}")
                    tar.add(filename, arcname=filename, recursive=False, filter=reset_tar_info)
    return output_path

def get_sha256(filepath):
    """Calculate SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def build_and_hash():
    """Build artifact once in a temp directory and return SHA-256 hash and path."""
    tmpdir = tempfile.mkdtemp()
    try:
        artifact_path = os.path.join(tmpdir, OUTPUT_NAME)
        create_artifact(artifact_path)
        digest = get_sha256(artifact_path)
        return digest, artifact_path
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)

def main():
    """Run two builds and compare their SHA-256 hashes."""
    print("=== ZeroShrink Reproducible Build ===\n")
    
    # Build 1
    print("=== Build 1 ===")
    print(f"Creating artifact: {OUTPUT_NAME}")
    print("Included files:")
    for f in sorted(SOURCE_FILES):
        print(f"  - {f}")
    
    try:
        hash1, _ = build_and_hash()
        print(f"SHA-256: {hash1}\n")
    except Exception as e:
        print(f"Error during Build 1: {e}", file=sys.stderr)
        return 1

    # Build 2
    print("=== Build 2 ===")
    print(f"Creating artifact: {OUTPUT_NAME}")
    print("Included files:")
    for f in sorted(SOURCE_FILES):
        print(f"  - {f}")
        
    try:
        hash2, _ = build_and_hash()
        print(f"SHA-256: {hash2}\n")
    except Exception as e:
        print(f"Error during Build 2: {e}", file=sys.stderr)
        return 1

    # Comparison
    print("=== Comparison ===")
    if hash1 == hash2:
        print("✅ Artifacts match! Build is reproducible.")
        return 0
    else:
        print("❌ Artifacts differ! Build is NOT reproducible.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
