import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
import argparse
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
# 0. HELPER FUNCTIONS FOR PATH RESOLUTION
# =============================================================================

# NEW: Helper function to resolve final output path given base path, user dir, and extension.
def resolve_output_path(base_path, user_dir=None, extension=""):
    """
    Determines the final destination path for compressed or extracted files.
    If user_dir is omitted or None, defaults to current working directory.
    Creates destination directory using os.makedirs if it does not exist.
    """
    dest_dir = user_dir if user_dir else os.getcwd()
    if not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)
    filename = os.path.basename(base_path)
    if extension and not filename.endswith(extension):
        filename += extension
    return os.path.join(dest_dir, filename)


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

        crc32_val = zlib.crc32(data) & 0xFFFFFFFF
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
# 3. GUI LAYER (Super-Responsive Dark Theme with Destination Directory Pickers)
# =============================================================================

class ZeroShrinkGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZeroShrink - Lossless Studio")
        self.root.geometry("920x620")
        self.root.configure(bg="#232323")

        self.engine = ZeroShrinkEngine()
        self.history_file = "zshrink_history.json"
        self.history = self.load_history()

        # NEW: Destination folder variables defaulting to current working directory
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        self.extract_dir_var = tk.StringVar(value=os.getcwd())

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

        style.configure("Custom.Horizontal.TProgressbar",
                        troughcolor="#2d2d2d",
                        background="#4a90e2",
                        thickness=14,
                        bordercolor="#232323")

        # Top Toolbar
        toolbar = tk.Frame(self.root, bg="#2d2d2d")
        toolbar.pack(side="top", fill="x", padx=20, pady=(15, 5))

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

        # NEW: Destination Folders Selection Toolbar
        dest_frame = tk.Frame(self.root, bg="#2d2d2d", pady=8, padx=15)
        dest_frame.pack(side="top", fill="x", padx=20, pady=(5, 10))

        # Compression Output Folder Controls
        lbl_comp = tk.Label(dest_frame, text="Destination Folder:", bg="#2d2d2d", fg="#cccccc", font=("Segoe UI", 9, "bold"))
        lbl_comp.grid(row=0, column=0, sticky="w", padx=(0, 5), pady=3)

        entry_comp = tk.Entry(dest_frame, textvariable=self.output_dir_var, bg="#333333", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9))
        entry_comp.grid(row=0, column=1, sticky="ew", padx=5, pady=3)

        btn_browse_comp = tk.Button(dest_frame, text="Browse", command=self.browse_output_dir, bg="white", fg="black", relief="flat", padx=10, font=("Segoe UI", 8, "bold"), cursor="hand2")
        btn_browse_comp.grid(row=0, column=2, padx=(5, 20), pady=3)

        # Decompression Extraction Folder Controls
        lbl_ext = tk.Label(dest_frame, text="Extract To:", bg="#2d2d2d", fg="#cccccc", font=("Segoe UI", 9, "bold"))
        lbl_ext.grid(row=0, column=3, sticky="w", padx=(0, 5), pady=3)

        entry_ext = tk.Entry(dest_frame, textvariable=self.extract_dir_var, bg="#333333", fg="white", insertbackground="white", relief="flat", font=("Segoe UI", 9))
        entry_ext.grid(row=0, column=4, sticky="ew", padx=5, pady=3)

        btn_browse_ext = tk.Button(dest_frame, text="Browse", command=self.browse_extract_dir, bg="white", fg="black", relief="flat", padx=10, font=("Segoe UI", 8, "bold"), cursor="hand2")
        btn_browse_ext.grid(row=0, column=5, padx=(5, 0), pady=3)

        dest_frame.columnconfigure(1, weight=1)
        dest_frame.columnconfigure(4, weight=1)

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

    # NEW: Browse folder dialog handler for compression destination
    def browse_output_dir(self):
        folder = filedialog.askdirectory(initialdir=self.output_dir_var.get())
        if folder:
            self.output_dir_var.set(folder)

    # NEW: Browse folder dialog handler for decompression extraction destination
    def browse_extract_dir(self):
        folder = filedialog.askdirectory(initialdir=self.extract_dir_var.get())
        if folder:
            self.extract_dir_var.set(folder)

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
            
            # CHANGED: Use resolve_output_path to place output in selected destination folder
            target_dir = self.output_dir_var.get()
            save_path = resolve_output_path(path, target_dir, ".zshrink")

            with open(save_path, 'wb') as f:
                f.write(compressed)

            orig_size = len(data)
            comp_size = len(compressed)
            ratio = (comp_size / orig_size * 100) if orig_size > 0 else 0

            record = {
                "id": len(self.history) + 1,
                "filename": os.path.basename(save_path),
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
        messagebox.showinfo("Success", f"File compressed to:\n{record['path']}")

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

        # CHANGED: Use selected extraction folder as initial directory in filedialog or default extract path
        target_dir = self.extract_dir_var.get()
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        default_name = record['filename']
        if default_name.endswith(".zshrink"):
            default_name = default_name[:-8]
        elif default_name.endswith(".zc"):
            default_name = default_name[:-3]

        save_path = filedialog.asksaveasfilename(
            title="Save Decompressed File",
            initialdir=target_dir,
            initialfile=default_name
        )
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
            self.root.after(0, self._on_extract_done, save_path)
        except Exception as e:
            self.root.after(0, self._on_worker_error, str(e))

    def _on_extract_done(self, save_path):
        self.set_busy(False, "✔ File extracted successfully!")
        messagebox.showinfo("Success", f"File extracted to:\n{save_path}")

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


# =============================================================================
# 4. CLI AND ENTRY POINT
# =============================================================================

# NEW: CLI Entry Point & Subcommand Processing
def main():
    parser = argparse.ArgumentParser(description="ZeroShrink - Zero-Dependency Lossless Compression Studio")
    subparsers = parser.add_subparsers(dest="command", help="Subcommands: compress, decompress")

    # Compress subcommand
    compress_parser = subparsers.add_parser("compress", help="Compress a file")
    compress_parser.add_argument("file", help="Path to input file")
    compress_parser.add_argument("-o", "--output-dir", help="Destination folder for compressed file", default=None)

    # Decompress subcommand
    decompress_parser = subparsers.add_parser("decompress", help="Decompress an archive")
    decompress_parser.add_argument("file", help="Path to archive file (.zshrink or .zc)")
    decompress_parser.add_argument("-x", "--extract-dir", help="Destination folder for extracted file", default=None)
    decompress_parser.add_argument("-out", "--output", help="Explicit output filename (optional)", default=None)

    args = parser.parse_args()

    if args.command == "compress":
        engine = ZeroShrinkEngine()
        input_path = args.file
        if not os.path.exists(input_path):
            print(f"Error: File '{input_path}' not found.", file=sys.stderr)
            sys.exit(1)

        with open(input_path, "rb") as f:
            data = f.read()

        compressed, codec_type = engine.compress(data, return_type=True)
        
        # Check if output file has .zshrink or .zc extension
        out_path = resolve_output_path(input_path, args.output_dir, ".zshrink")

        with open(out_path, "wb") as f:
            f.write(compressed)

        print(f"Compressed '{input_path}' -> '{out_path}' ({len(data)} -> {len(compressed)} bytes, Codec: {codec_type})")
        sys.exit(0)

    elif args.command == "decompress":
        engine = ZeroShrinkEngine()
        archive_path = args.file
        if not os.path.exists(archive_path):
            print(f"Error: Archive file '{archive_path}' not found.", file=sys.stderr)
            sys.exit(1)

        with open(archive_path, "rb") as f:
            archive = f.read()

        decompressed = engine.decompress(archive)

        base_name = os.path.basename(archive_path)
        if base_name.endswith(".zshrink"):
            orig_name = base_name[:-8]
        elif base_name.endswith(".zc"):
            orig_name = base_name[:-3]
        else:
            orig_name = base_name + ".extracted"

        if args.output:
            orig_name = os.path.basename(args.output)

        target_dir = args.extract_dir if args.extract_dir else os.getcwd()
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        out_path = os.path.join(target_dir, orig_name)
        with open(out_path, "wb") as f:
            f.write(decompressed)

        print(f"Decompressed '{archive_path}' -> '{out_path}' ({len(decompressed)} bytes)")
        sys.exit(0)

    else:
        # Launch GUI if no subcommand is passed
        root = tk.Tk()
        app = ZeroShrinkGUI(root)
        root.mainloop()


if __name__ == "__main__":
    main()
