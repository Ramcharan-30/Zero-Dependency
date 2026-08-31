import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import struct
import pickle
import zlib
import lzma
import bz2
import json
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
        candidates = [
            (None, 0, "Store"), (None, 1, "Zlib"), (None, 2, "LZMA"), (None, 3, "BZ2"), (None, 4, "Huffman"),
            (Transforms.delta8, 0, "Delta+Store"), (Transforms.delta8, 1, "Delta+Zlib"), (Transforms.delta8, 2, "Delta+LZMA"),
            (Transforms.delta8, 3, "Delta+BZ2"), (Transforms.delta8, 4, "Delta+Huffman")
        ]

        best_payload = None
        best_score = float('inf')
        best_config = None
        best_type = ""

        for trans, codec, type_name in candidates:
            processed = trans(data) if trans else data

            if codec == 0: payload = processed
            elif codec == 1: payload = zlib.compress(processed)
            elif codec == 2: payload = lzma.compress(processed)
            elif codec == 3: payload = bz2.compress(processed)
            elif codec == 4:
                payload, _ = self.huffman.compress(processed)
                payload = pickle.dumps(_) + struct.pack("I", 0) + payload

            if len(payload) < best_score:
                best_score = len(payload)
                best_payload = payload
                best_config = (trans, codec)
                best_type = type_name

        trans_id = 1 if best_config[0] == Transforms.delta8 else 0
        codec_id = best_config[1]
        header = struct.pack(">4sBBQ", b"ZSRK", trans_id, codec_id, len(data))

        if codec_id == 4:
            processed = best_config[0](data) if best_config[0] else data
            payload, mapping = self.huffman.compress(processed)
            mapping_bytes = pickle.dumps(mapping)
            padding = 8 - (len("".join([self.huffman.codes[s] for s in processed])) % 8) if len("".join([self.huffman.codes[s] for s in processed])) % 8 != 0 else 0
            huff_header = struct.pack(">IB", len(mapping_bytes), padding) + mapping_bytes
            final_payload = huff_header + payload
        else:
            final_payload = best_payload

        return header + final_payload, best_type

    def decompress(self, archive):
        if len(archive) < 14: raise ValueError("Invalid archive")
        magic, trans_id, codec_id, orig_size = struct.unpack(">4sBBQ", archive[:14])
        if magic != b"ZSRK": raise ValueError("Not a ZeroShrink archive")

        payload = archive[14:]
        if codec_id == 4:
            meta_len, padding = struct.unpack(">IB", payload[:5])
            mapping = pickle.loads(payload[5:5+meta_len])
            data = self.huffman.decompress(payload[5+meta_len:], mapping, padding)
        elif codec_id == 0: data = payload
        elif codec_id == 1: data = zlib.decompress(payload)
        elif codec_id == 2: data = lzma.decompress(payload)
        elif codec_id == 3: data = bz2.decompress(payload)
        else: raise ValueError("Unknown codec")

        if trans_id == 1: data = Transforms.undelta8(data)
        return data

# =============================================================================
# 3. GUI LAYER (Updated to match high-contrast screenshot)
# =============================================================================

class ZeroShrinkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZeroShrink - Lossless Studio")
        self.root.geometry("900x550")
        self.root.configure(bg="#232323") # Deep dark background

        self.engine = ZeroShrinkEngine()
        self.history_file = "zshrink_history.json"
        self.history = self.load_history()

        self.setup_ui()
        self.refresh_table()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except: return []
        return []

    def save_history(self):
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=4)

    def setup_ui(self):
        # Styling
        style = ttk.Style()
        style.theme_use('clam')

        # Table (Treeview) Styling - Matches the dark grey appearance
        style.configure("Treeview",
                        background="#333333",
                        foreground="white",
                        fieldbackground="#333333",
                        rowheight=28,
                        font=("Segoe UI", 10))
        style.configure("Treeview.Heading",
                        background="#2d2d2d",
                        foreground="#cccccc",
                        relief="flat",
                        font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', '#4a90e2')])

        # Top Toolbar - Slightly lighter than main bg
        toolbar = tk.Frame(self.root, bg="#2d2d2d")
        toolbar.pack(side="top", fill="x", padx=20, pady=15)

        # High Contrast White Buttons as per second screenshot
        btn_style = {
            "bg": "white",
            "fg": "black",
            "relief": "flat",
            "padx": 15,
            "pady": 5,
            "font": ("Segoe UI", 9, "bold")
        }

        self.btn_compress = tk.Button(toolbar, text="Compress File", command=self.handle_compress, **btn_style)
        self.btn_compress.pack(side="left", padx=5)

        self.btn_extract = tk.Button(toolbar, text="Extract Selected", command=self.handle_extract, **btn_style)
        self.btn_extract.pack(side="left", padx=5)

        self.btn_delete = tk.Button(toolbar, text="Delete Record", command=self.handle_delete, **btn_style)
        self.btn_delete.pack(side="left", padx=5)

        self.btn_refresh = tk.Button(toolbar, text="Refresh", command=self.refresh_table, **btn_style)
        self.btn_refresh.pack(side="right", padx=5)

        # Main Table Area
        table_frame = tk.Frame(self.root, bg="#232323")
        table_frame.pack(expand=True, fill="both", padx=20, pady=10)

        columns = ("id", "filename", "original", "compressed", "ratio", "type")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings")

        self.tree.heading("id", text="Id")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("original", text="Original")
        self.tree.heading("compressed", text="Compressed")
        self.tree.heading("ratio", text="Ratio")
        self.tree.heading("type", text="Type")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("filename", width=350, anchor="w")
        self.tree.column("original", width=120, anchor="center")
        self.tree.column("compressed", width=120, anchor="center")
        self.tree.column("ratio", width=120, anchor="center")
        self.tree.column("type", width=120, anchor="center")

        self.tree.pack(expand=True, fill="both")

    def refresh_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        for item in self.history:
            self.tree.insert("", "end", values=(
                item['id'],
                item['filename'],
                item['original'],
                item['compressed'],
                item['ratio'],
                item['type']
            ))

    def handle_compress(self):
        path = filedialog.askopenfilename()
        if not path: return
        try:
            with open(path, 'rb') as f: data = f.read()
            compressed, codec_type = self.engine.compress(data)

            filename = os.path.basename(path)
            save_path = os.path.join(os.path.dirname(path), filename + ".zshrink")

            with open(save_path, 'wb') as f: f.write(compressed)

            orig_size = len(data)
            comp_size = len(compressed)
            ratio = (comp_size / orig_size * 100) if orig_size > 0 else 0

            record_id = len(self.history) + 1
            self.history.append({
                "id": record_id,
                "filename": filename + ".zshrink",
                "original": f"{orig_size / 1024:.2f} KB",
                "compressed": f"{comp_size / 1024:.2f} KB",
                "ratio": f"{ratio:.2f}%",
                "type": codec_type,
                "path": save_path
            })
            self.save_history()
            self.refresh_table()
            messagebox.showinfo("Success", "File compressed and recorded!")

        except Exception as e: messagebox.showerror("Error", str(e))

    def handle_extract(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a record to extract.")
            return

        item_values = self.tree.item(selected[0])['values']
        record_id = item_values[0]

        record = next((x for x in self.history if x['id'] == record_id), None)
        if not record: return

        try:
            with open(record['path'], 'rb') as f: archive = f.read()
            decompressed = self.engine.decompress(archive)

            save_path = filedialog.asksaveasfilename(title="Save Decompressed File")
            if save_path:
                with open(save_path, 'wb') as f: f.write(decompressed)
                messagebox.showinfo("Success", "File extracted successfully!")
        except Exception as e: messagebox.showerror("Error", str(e))

    def handle_delete(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a record to delete.")
            return

        item_values = self.tree.item(selected[0])['values']
        record_id = item_values[0]

        if messagebox.askyesno("Confirm", "Delete this record from history?"):
            self.history = [x for x in self.history if x['id'] != record_id]
            self.save_history()
            self.refresh_table()

if __name__ == "__main__":
    root = tk.Tk()
    app = ZeroShrinkGUI(root)
    root.mainloop()
