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
import json
import threading
import time
from collections import Counter
import heapq

# =============================================================================
# 1. CORE CODECS & TRANSFORMS (The "Package Killer" Logic)
# =============================================================================

class HuffmanCoder:
    def __init__(self):
        self.reverse_mapping = {}

    def compress(self, data):
        if not data:
            return b"", {}, 0
        freq = Counter(data)

        # Single symbol edge case (e.g. b"AAAAA")
        if len(freq) == 1:
            symbol = next(iter(freq))
            reverse_mapping = {"0": symbol}
            bit_count = len(data)
            padding = (8 - (bit_count % 8)) % 8
            byte_len = (bit_count + padding) // 8
            payload = bytes(byte_len)  # All zeros represent bit '0'
            return payload, reverse_mapping, padding

        heap = [[weight, [symbol, ""]] for symbol, weight in freq.items()]
        heapq.heapify(heap)
        while len(heap) > 1:
            lo = heapq.heappop(heap)
            hi = heapq.heappop(heap)
            for pair in lo[1:]:
                pair[1] = '0' + pair[1]
            for pair in hi[1:]:
                pair[1] = '1' + pair[1]
            heapq.heappush(heap, [lo[0] + hi[0]] + lo[1:] + hi[1:])

        huff_list = sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]), p))

        # Build integer bit values for fast packing without string manipulation
        code_table = {}
        str_codes = {}
        for symbol, code_str in huff_list:
            code_table[symbol] = (int(code_str, 2), len(code_str))
            str_codes[code_str] = symbol

        self.reverse_mapping = str_codes

        # Bit packing using integer bit buffer
        out_bytes = bytearray()
        bit_buffer = 0
        bit_count = 0

        for byte_val in data:
            val, length = code_table[byte_val]
            bit_buffer = (bit_buffer << length) | val
            bit_count += length
            while bit_count >= 8:
                bit_count -= 8
                out_bytes.append((bit_buffer >> bit_count) & 0xFF)

        padding = 0
        if bit_count > 0:
            padding = 8 - bit_count
            bit_buffer = bit_buffer << padding
            out_bytes.append(bit_buffer & 0xFF)

        return bytes(out_bytes), self.reverse_mapping, padding

    def decompress(self, data, mapping, padding):
        if not data:
            return b""

        # Build prefix tree for fast bit stream decoding
        root = {}
        for code_str, symbol in mapping.items():
            curr = root
            for bit in code_str[:-1]:
                if bit not in curr:
                    curr[bit] = {}
                curr = curr[bit]
            curr[code_str[-1]] = symbol

        decoded_data = bytearray()
        total_bits = len(data) * 8 - padding
        bits_read = 0
        curr = root

        for byte_val in data:
            for shift in (7, 6, 5, 4, 3, 2, 1, 0):
                if bits_read >= total_bits:
                    break
                bit_char = '1' if (byte_val & (1 << shift)) else '0'
                bits_read += 1

                curr = curr[bit_char]
                if isinstance(curr, int):
                    decoded_data.append(curr)
                    curr = root

        return bytes(decoded_data)


class Transforms:
    @staticmethod
    def delta8(data):
        if not data:
            return b""
        out = bytearray(len(data))
        out[0] = data[0]
        out[1:] = bytes((b - a) & 0xFF for a, b in zip(data[:-1], data[1:]))
        return bytes(out)

    @staticmethod
    def undelta8(data):
        if not data:
            return b""
        out = bytearray(len(data))
        curr = data[0]
        out[0] = curr
        for i in range(1, len(data)):
            curr = (data[i] + curr) & 0xFF
            out[i] = curr
        return bytes(out)


# =============================================================================
# 2. ADAPTIVE STRATEGY & ARCHIVE
# =============================================================================

class ZeroShrinkEngine:
    CODEC_NAMES = {0: "Store", 1: "Zlib", 2: "LZMA", 3: "BZ2", 4: "Huffman"}

    def __init__(self):
        self.huffman = HuffmanCoder()

    def _encode_candidate(self, processed, codec):
        if codec == 0:
            return processed, None, 0
        elif codec == 1:
            return zlib.compress(processed, level=6), None, 0
        elif codec == 2:
            # Preset 3 provides fast, high-ratio LZMA compression without freezing
            return lzma.compress(processed, preset=3), None, 0
        elif codec == 3:
            return bz2.compress(processed, compresslevel=6), None, 0
        elif codec == 4:
            payload, mapping, padding = self.huffman.compress(processed)
            mapping_bytes = pickle.dumps(mapping)
            full_huff_payload = struct.pack(">IB", len(mapping_bytes), padding) + mapping_bytes + payload
            return full_huff_payload, mapping, padding
        raise ValueError(f"Unknown codec {codec}")

    def get_codec_description(self, trans_id, codec_id):
        trans_prefix = "Delta+" if trans_id == 1 else ""
        codec_name = self.CODEC_NAMES.get(codec_id, "Unknown")
        return f"{trans_prefix}{codec_name}"

    def compress(self, data, return_type=False, status_callback=None):
        candidates = [
            (None, 0), (None, 1), (None, 2), (None, 3), (None, 4),
            (Transforms.delta8, 0), (Transforms.delta8, 1), (Transforms.delta8, 2),
            (Transforms.delta8, 3), (Transforms.delta8, 4)
        ]

        # Fast 64 KB sampling for candidate evaluation on large files
        SAMPLE_SIZE = 64 * 1024
        if len(data) > SAMPLE_SIZE:
            eval_data = data[:SAMPLE_SIZE]
        else:
            eval_data = data

        best_score = float('inf')
        best_config = candidates[0]

        if status_callback:
            status_callback("Evaluating compression strategies...")

        for trans, codec in candidates:
            # Micro-sleep to yield Python GIL to main Tkinter thread for smooth GUI repaints
            time.sleep(0.005)
            proc_eval = trans(eval_data) if trans else eval_data
            try:
                payload_eval, _, _ = self._encode_candidate(proc_eval, codec)
                score = len(payload_eval)
                if score < best_score:
                    best_score = score
                    best_config = (trans, codec)
            except Exception:
                continue

        best_trans, best_codec = best_config
        trans_id = 1 if best_trans == Transforms.delta8 else 0
        codec_id = best_codec
        type_desc = self.get_codec_description(trans_id, codec_id)

        if status_callback:
            status_callback(f"Compressing using optimal codec: {type_desc}...")

        time.sleep(0.005)
        processed_full = best_trans(data) if best_trans else data
        final_payload, _, _ = self._encode_candidate(processed_full, best_codec)

        # CRC32 checksum for payload integrity verification
        crc32_val = zlib.crc32(data) & 0xFFFFFFFF

        # Archive Header: [MAGIC 4B][TRANS_ID 1B][CODEC_ID 1B][ORIG_SIZE 8B][CRC32 4B]
        header = struct.pack(">4sBBQI", b"ZSRK", trans_id, codec_id, len(data), crc32_val)
        archive_bytes = header + final_payload

        if return_type:
            return archive_bytes, type_desc
        return archive_bytes

    def decompress(self, archive, status_callback=None):
        if status_callback:
            status_callback("Reading archive header...")

        if len(archive) < 18:
            if len(archive) >= 14:
                magic, trans_id, codec_id, orig_size = struct.unpack(">4sBBQ", archive[:14])
                if magic == b"ZSRK":
                    payload = archive[14:]
                    expected_crc = None
                else:
                    raise ValueError("Not a ZeroShrink archive")
            else:
                raise ValueError("Invalid archive header length")
        else:
            magic, trans_id, codec_id, orig_size, expected_crc = struct.unpack(">4sBBQI", archive[:18])
            if magic != b"ZSRK":
                raise ValueError("Not a ZeroShrink archive")
            payload = archive[18:]

        type_desc = self.get_codec_description(trans_id, codec_id)
        if status_callback:
            status_callback(f"Decompressing payload ({type_desc})...")

        time.sleep(0.005)
        if codec_id == 4:  # Huffman
            if len(payload) < 5:
                raise ValueError("Corrupt Huffman archive payload")
            meta_len, padding = struct.unpack(">IB", payload[:5])
            mapping = pickle.loads(payload[5:5 + meta_len])
            data = self.huffman.decompress(payload[5 + meta_len:], mapping, padding)
        elif codec_id == 0:
            data = payload
        elif codec_id == 1:
            data = zlib.decompress(payload)
        elif codec_id == 2:
            data = lzma.decompress(payload)
        elif codec_id == 3:
            data = bz2.decompress(payload)
        else:
            raise ValueError(f"Unknown codec ID {codec_id}")

        if trans_id == 1:
            data = Transforms.undelta8(data)

        if len(data) != orig_size:
            raise ValueError("Decompressed size mismatch")

        if expected_crc is not None:
            actual_crc = zlib.crc32(data) & 0xFFFFFFFF
            if actual_crc != expected_crc:
                raise ValueError("Archive integrity check failed (CRC32 mismatch)")

        return data


# =============================================================================
# 3. GUI LAYER (Super-Responsive Dark Theme with Loading Bar)
# =============================================================================

class ZeroShrinkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZeroShrink - Lossless Studio")
        self.root.geometry("900x580")
        self.root.configure(bg="#232323")

        self.engine = ZeroShrinkEngine()
        self.history_file = "zshrink_history.json"
        self.history = self.load_history()

        self.is_processing = False

        self.setup_ui()
        self.refresh_table()

    def load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def save_history(self):
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=4)
        except Exception:
            pass

    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')

        # Treeview Styling - Matches dark studio layout
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

        # Progressbar Styling
        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#2d2d2d",
                        background="#4a90e2",
                        thickness=14,
                        bordercolor="#232323")

        # Top Toolbar
        toolbar = tk.Frame(self.root, bg="#2d2d2d")
        toolbar.pack(side="top", fill="x", padx=20, pady=15)

        btn_style = {
            "bg": "white",
            "fg": "black",
            "relief": "flat",
            "padx": 15,
            "pady": 5,
            "font": ("Segoe UI", 9, "bold"),
            "cursor": "hand2"
        }

        self.btn_compress = tk.Button(toolbar, text="Compress File", command=self.handle_compress, **btn_style)
        self.btn_compress.pack(side="left", padx=5)

        self.btn_extract = tk.Button(toolbar, text="Extract Selected", command=self.handle_extract, **btn_style)
        self.btn_extract.pack(side="left", padx=5)

        self.btn_delete = tk.Button(toolbar, text="Delete Record", command=self.handle_delete, **btn_style)
        self.btn_delete.pack(side="left", padx=5)

        self.btn_refresh = tk.Button(toolbar, text="Refresh", command=self.refresh_table, **btn_style)
        self.btn_refresh.pack(side="right", padx=5)

        # Table Area
        table_frame = tk.Frame(self.root, bg="#232323")
        table_frame.pack(expand=True, fill="both", padx=20, pady=5)

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

        # Bottom Progress & Status Bar
        self.status_bar = tk.Frame(self.root, bg="#2d2d2d", pady=8, padx=15)
        self.status_bar.pack(side="bottom", fill="x")

        self.progress = ttk.Progressbar(self.status_bar, style="Custom.Horizontal.TProgressbar", mode='indeterminate')
        self.progress.pack(side="top", fill="x", expand=True, pady=(0, 5))

        self.status_var = tk.StringVar(value="Ready.")
        self.status_label = tk.Label(self.status_bar, textvariable=self.status_var, bg="#2d2d2d", fg="#e0e0e0", font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left")

    def set_busy(self, busy=True, message="Processing..."):
        self.is_processing = busy
        self.status_var.set(message)

        if busy:
            self.progress.start(12)
            self.btn_compress.config(state="disabled")
            self.btn_extract.config(state="disabled")
            self.btn_delete.config(state="disabled")
            self._pump_gui()
        else:
            self.progress.stop()
            self.btn_compress.config(state="normal")
            self.btn_extract.config(state="normal")
            self.btn_delete.config(state="normal")

    def _pump_gui(self):
        if self.is_processing:
            try:
                self.root.update_idletasks()
            except Exception:
                pass
            self.root.after(30, self._pump_gui)

    def update_status(self, text):
        self.root.after(0, lambda: self.status_var.set(text))

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
        if not path:
            return

        self.set_busy(True, f"⌛ Compressing {os.path.basename(path)}...")
        threading.Thread(target=self._worker_compress, args=(path,), daemon=True).start()

    def _worker_compress(self, path):
        try:
            with open(path, 'rb') as f:
                data = f.read()

            compressed, codec_type = self.engine.compress(
                data,
                return_type=True,
                status_callback=self.update_status
            )
            filename = os.path.basename(path)
            save_path = os.path.join(os.path.dirname(path), filename + ".zshrink")

            with open(save_path, 'wb') as f:
                f.write(compressed)

            orig_size = len(data)
            comp_size = len(compressed)
            ratio = (comp_size / orig_size * 100) if orig_size > 0 else 0

            record = {
                "id": len(self.history) + 1,
                "filename": filename + ".zshrink",
                "original": f"{orig_size / 1024:.2f} KB",
                "compressed": f"{comp_size / 1024:.2f} KB",
                "ratio": f"{ratio:.2f}%",
                "type": codec_type,
                "path": save_path
            }

            self.root.after(0, self._on_compress_done, record, orig_size, comp_size)
        except Exception as e:
            self.root.after(0, self._on_worker_error, str(e))

    def _on_compress_done(self, record, orig_size, comp_size):
        self.history.append(record)
        self.save_history()
        self.refresh_table()
        self.set_busy(False, f"✔ Compressed {orig_size / 1024:.1f}KB -> {comp_size / 1024:.1f}KB ({record['type']})")
        messagebox.showinfo("Success", "File compressed and recorded successfully!")

    def handle_extract(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection", "Please select a record to extract.")
            return

        item_values = self.tree.item(selected[0])['values']
        record_id = item_values[0]

        record = next((x for x in self.history if x['id'] == record_id), None)
        if not record:
            return

        save_path = filedialog.asksaveasfilename(title="Save Decompressed File")
        if not save_path:
            return

        self.set_busy(True, f"⌛ Extracting {record['filename']}...")
        threading.Thread(target=self._worker_extract, args=(record['path'], save_path), daemon=True).start()

    def _worker_extract(self, archive_path, save_path):
        try:
            with open(archive_path, 'rb') as f:
                archive = f.read()
            decompressed = self.engine.decompress(
                archive,
                status_callback=self.update_status
            )
            with open(save_path, 'wb') as f:
                f.write(decompressed)
            self.root.after(0, self._on_extract_done)
        except Exception as e:
            self.root.after(0, self._on_worker_error, str(e))

    def _on_extract_done(self):
        self.set_busy(False, "✔ File extracted successfully!")
        messagebox.showinfo("Success", "File extracted successfully!")

    def _on_worker_error(self, err_msg):
        self.set_busy(False, "❌ Error encountered.")
        messagebox.showerror("Error", err_msg)

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
            self.status_var.set("Record deleted.")


if __name__ == "__main__":
    root = tk.Tk()
    app = ZeroShrinkGUI(root)
    root.mainloop()
