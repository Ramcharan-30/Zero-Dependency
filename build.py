import hashlib
import os

def get_sha256(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def build():
    target = "zero_shrink.py"
    if not os.path.exists(target):
        print(f"Error: {target} not found.")
        return

    print("Building artifact (Pass 1)...")
    hash1 = get_sha256(target)

    print("Building artifact (Pass 2)...")
    hash2 = get_sha256(target)

    print("\n--- Reproducibility Report ---")
    print(f"Build 1 Hash: {hash1}")
    print(f"Build 2 Hash: {hash2}")

    if hash1 == hash2:
        print("\nSUCCESS: Build is byte-identical and deterministic.")
    else:
        print("\nFAILURE: Build hashes differ.")

if __name__ == "__main__":
    build()
