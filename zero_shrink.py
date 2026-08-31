import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import struct
import pickle
import zlib
import lzma
import bz2
import hashlib
import binascii
from collections import Counter
import heapq

# =============================================================================
# 1. CORE CODECS & TRANSFORMS (The "Package Killer" Logic)
# =============================================================================

class HuffmanCoder:
    def __init__(self):
        self.reverse_mapping = {}

    def compress(self, data):
        if not data: return b"", {}
        freq = Counter(data)
        heap = [[weight, [symbol, ""]] for symbol, weight in freq.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]: pair[1] = '0' + pair[1]
            for pair in hi[1:]: pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])

        huff_list = sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))
        codes = {symbol: code for symbol, code in huff_list}
        self.reverse_mapping = {code: symbol for symbol, code in huff_list}

        encoded_text = "".join([codes[symbol] for symbol in data])
        padding = 8 - (len(encoded_text) % 8) if len(encoded_text) % 8 != 0 else 0
        encoded_text += "0" * padding

        byte_array = bytearray()
        for i in range(0, len(encoded_text), 8):
            byte_array.append(int(encoded_text[i:i+8], 2))

        return bytes(byte_array), self.reverse_mapping

    def decompress(self, data, mapping, padding):
        if not data: return b""
        bit_string = "".join([bin(byte)[2:].zfill(8) for byte in data])
        if padding > 0: bit_string = bit_string[:-padding]

        decoded_data = bytearray()
        current_code = ""
        for bit in bit_string:
            current_code += bit
            if current_code in mapping:
                decoded_data.append(mapping[current_code])
                current_code = ""
        return bytes(decoded_data)

class Transforms:
    @staticmethod
    def delta8(data):
        if not data: return b""
        out = bytearray([data[0]])
        for i in range(1, len(data)):
            out.append((data[i] - data[i-1]) & 0xFF)
        return bytes(out)

    @staticmethod
    def undelta8(data):
        if not data: return b""
        out = bytearray([data[0]])
        for i in range(1, len(data)):
            out.append((data[i] + out[-1]) & 0xFF)
        return bytes(out)

# =============================================================================
# 2. ADAPTIVE STRATEGY & ARCHIVE
# =============================================================================

class ZeroShrinkEngine:
    def __init__(self):
        self.huffman = HuffmanCoder()

    def compress(self, data):
        # Candidates: (Transform, Codec)
        # Codecs: 0: Store, 1: Zlib, 2: LZMA, 3: BZ2, 4: Huffman
        candidates = [
            (None, 0), (None, 1), (None, 2), (None, 3), (None, 4),
            (Transforms.delta8, 0), (Transforms.delta8, 1), (Transforms.delta8, 2),
            (Transforms.delta8, 3), (Transforms.delta8, 4)
        ]

        best_payload = None
        best_meta = None
        best_score = float('inf')
        best_config = None

        for trans, codec in candidates:
            processed = trans(data) if trans else data

            if codec == 0: payload = processed
            elif codec == 1: payload = zlib.compress(processed)
            elif codec == 2: payload = lzma.compress(processed)
            elif codec == 3: payload = bz2.compress(processed)
            elif codec == 4:
                payload, mapping = self.huffman.compress(processed)
                # We need to store the mapping as part of the payload for scoring
                payload = pickle.dumps(mapping) + struct.pack("I", 0) + payload # Simplified

            if len(payload) < best_score:
                best_score = len(payload)
                best_payload = payload
                best_config = (trans, codec)

        # Final Archive Construction (.zshrink)
        # Layout: [MAGIC 4B][TRANS_ID 1B][CODEC_ID 1B][ORIG_SIZE 8B][PAYLOAD]
        trans_id = 1 if best_config[0] == Transforms.delta8 else 0
        codec_id = best_config[1]

        header = struct.pack(">4sBBQ", b"ZSRK", trans_id, codec_id, len(data))

        # If Huffman, we need to embed the mapping properly
        if codec_id == 4:
            # Re-run to get clean metadata
            processed = best_config[0](data) if best_config[0] else data
            payload, mapping = self.huffman.compress(processed)
            mapping_bytes = pickle.dumps(mapping)
            padding = 8 - (len("".join([self.huffman.codes[s] for s in processed])) % 8) if len("".join([self.huffman.codes[s] for s in processed])) % 8 != 0 else 0
            # Header for Huffman: [meta_len 4B][padding 1B][mapping][data]
            huff_header = struct.pack(">IB", len(mapping_bytes), padding) + mapping_bytes
            final_payload = huff_header + payload
        else:
            final_payload = best_payload

        return header + final_payload

    def decompress(self, archive):
        if len(archive) < 14: raise ValueError("Invalid archive")

        magic, trans_id, codec_id, orig_size = struct.unpack(">4sBBQ", archive[:14])
        if magic != b"ZSRK": raise ValueError("Not a ZeroShrink archive")

        payload = archive[14:]

        if codec_id == 4: # Huffman
            meta_len, padding = struct.unpack(">IB", payload[:5])
            mapping = pickle.loads(payload[5:5+meta_len])
            data = self.huffman.decompress(payload[5+meta_len:], mapping, padding)
        elif codec_id == 0: data = payload
        elif codec_id == 1: data = zlib.decompress(payload)
        elif codec_id == 2: data = lzma.decompress(payload)
        elif codec_id == 3: data = bz2.decompress(payload)
        else: raise ValueError("Unknown codec")

        if trans_id == 1:
            data = Transforms.undelta8(data)

        return data

# =============================================================================
# 3. GUI LAYER
# =============================================================================

class ZeroShrinkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZeroShrink - Lossless Studio")
        self.root.geometry("600x400")
        self.engine = ZeroShrinkEngine()
        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(expand=True, fill="both")

        ttk.Label(main_frame, text="ZeroShrink Adaptive Compression", font=("Segoe UI", 16, "bold")).pack(pady=20)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        ttk.Button(btn_frame, text="Compress", command=self.handle_compress).grid(row=0, column=0, padx=10)
        ttk.Button(btn_frame, text="Decompress", command=self.handle_decompress).grid(row=0, column=1, padx=10)

        self.status_var = tk.StringVar(value="Ready.")
        ttk.Label(main_frame, textvariable=self.status_var, wraplength=500).pack(pady=30)

    def handle_compress(self):
        path = filedialog.askopenfilename()
        if not path: return
        try:
            with open(path, 'rb') as f: data = f.read()
            compressed = self.engine.compress(data)
            save_path = filedialog.asksaveasfilename(defaultextension=".zshrink")
            if save_path:
                with open(save_path, 'wb') as f: f.write(compressed)
                self.status_var.set(f"Compressed {len(data)} -> {len(compressed)} bytes")
        except Exception as e: messagebox.showerror("Error", str(e))

    def handle_decompress(self):
        path = filedialog.askopenfilename(filetypes=[("ZeroShrink", "*.zshrink")])
        if not path: return
        try:
            with open(path, 'rb') as f: data = f.read()
            decompressed = self.engine.decompress(data)
            save_path = filedialog.asksaveasfilename()
            if save_path:
                with open(save_path, 'wb') as f: f.write(decompressed)
                self.status_var.set("Decompressed successfully!")
        except Exception as e: messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = ZeroShrinkGUI(root)
    root.mainloop()
