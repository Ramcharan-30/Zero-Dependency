import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import queue

from .db import ArchiveDatabase
from .metrics import format_size, Timer
from .filesystem import get_downloads_path, get_safe_output_path
from .archive import create_archive, extract_archive
from .strategy import Profile, get_profile_name
from .errors import ArchiveValidationError

class ResultDialog(tk.Toplevel):
    def __init__(self, parent, title, message, details=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("400x300")
        self.configure(bg="#1e1e1e")
        self.transient(parent)
        self.grab_set()
        
        lbl = tk.Label(self, text=message, bg="#1e1e1e", fg="#569cd6", font=("Segoe UI", 12, "bold"))
        lbl.pack(pady=10)
        
        if details:
            text = tk.Text(self, bg="#252526", fg="#d4d4d4", font=("Consolas", 10), bd=0, padx=10, pady=10)
            text.pack(expand=True, fill="both", padx=10, pady=5)
            text.insert("1.0", details)
            text.config(state="disabled")
            
        btn = ttk.Button(self, text="Close", command=self.destroy)
        btn.pack(pady=10)


class ZeroShrinkGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZeroShrink - Lossless Studio")
        self.geometry("950x650")
        self.db = ArchiveDatabase()
        self.work_queue = queue.Queue()
        
        self.apply_dark_theme()
        self.setup_ui()
        self.refresh_data()
        
    def apply_dark_theme(self):
        style = ttk.Style(self)
        # Fallback to 'clam' to ensure consistent styling cross-platform
        if 'clam' in style.theme_names():
            style.theme_use('clam')
            
        bg_color = "#1e1e1e"
        fg_color = "#d4d4d4"
        sel_bg = "#094771"
        sel_fg = "#ffffff"
        btn_bg = "#333333"

        self.configure(bg=bg_color)
        style.configure("TFrame", background=bg_color)
        style.configure("TLabel", background=bg_color, foreground=fg_color, font=("Segoe UI", 10))
        
        style.configure("TButton", background=btn_bg, foreground=fg_color, font=("Segoe UI", 10), borderwidth=0, padding=5)
        style.map("TButton", background=[('active', "#444444")])
        
        style.configure("Treeview", 
            background="#252526", 
            foreground=fg_color, 
            fieldbackground="#252526", 
            borderwidth=0,
            font=("Segoe UI", 10))
        style.map("Treeview", background=[('selected', sel_bg)], foreground=[('selected', sel_fg)])
        
        style.configure("Treeview.Heading", 
            background="#2d2d2d", 
            foreground=fg_color, 
            borderwidth=1, 
            relief="flat",
            font=("Segoe UI", 10, "bold"))
        style.map("Treeview.Heading", background=[('active', "#3e3e42")])
        
        style.configure("Horizontal.TProgressbar", background="#0e70c0", troughcolor="#333333", borderwidth=0)


    def setup_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        
        # Toolbar
        toolbar = ttk.Frame(self, padding="10")
        toolbar.grid(row=0, column=0, sticky="ew")
        
        ttk.Button(toolbar, text="Compress File", command=self.compress_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Extract Selected", command=self.extract_selected).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Delete Record", command=self.delete_selected).pack(side=tk.LEFT, padx=5)
        
        self.progress = ttk.Progressbar(toolbar, mode="indeterminate", style="Horizontal.TProgressbar", length=150)
        self.progress.pack(side=tk.RIGHT, padx=10)
        
        ttk.Button(toolbar, text="Refresh", command=self.refresh_data).pack(side=tk.RIGHT, padx=5)
        
        # Treeview for database
        columns = ("id", "filename", "original", "compressed", "ratio", "profile", "date")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        
        self.tree.heading("id", text="ID")
        self.tree.heading("filename", text="Filename")
        self.tree.heading("original", text="Original")
        self.tree.heading("compressed", text="Compressed")
        self.tree.heading("ratio", text="Ratio")
        self.tree.heading("profile", text="Profile")
        self.tree.heading("date", text="Date")
        
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("filename", width=250)
        self.tree.column("original", width=100, anchor=tk.E)
        self.tree.column("compressed", width=100, anchor=tk.E)
        self.tree.column("ratio", width=100, anchor=tk.E)
        self.tree.column("profile", width=150)
        self.tree.column("date", width=150, anchor=tk.CENTER)
        
        self.tree.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.grid(row=1, column=1, sticky="ns", pady=10)

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        records = self.db.get_all_archives()
        for rec in records:
            ratio_str = f"{rec['ratio']:.2f}%"
            self.tree.insert("", tk.END, values=(
                rec["id"],
                rec["filename"],
                format_size(rec["original_size"]),
                format_size(rec["compressed_size"]),
                ratio_str,
                rec["profile"],
                rec["created_at"]
            ))

    def _set_loading_state(self, is_loading):
        if is_loading:
            self.progress.start(10)
            self.config(cursor="wait")
            for child in self.winfo_children():
                if isinstance(child, ttk.Frame):
                    for btn in child.winfo_children():
                        if isinstance(btn, ttk.Button):
                            btn.state(['disabled'])
        else:
            self.progress.stop()
            self.config(cursor="")
            for child in self.winfo_children():
                if isinstance(child, ttk.Frame):
                    for btn in child.winfo_children():
                        if isinstance(btn, ttk.Button):
                            btn.state(['!disabled'])

    def check_queue(self):
        try:
            msg_type, result = self.work_queue.get_nowait()
            self._set_loading_state(False)
            
            if msg_type == "compress_ok":
                filepath, out_path, orig_size, comp_size, profile_name, selection_result, elapsed = result
                self.db.add_archive(filepath.with_suffix('.zc').name, orig_size, comp_size, profile_name, str(out_path))
                self.refresh_data()
                
                ratio = (orig_size - comp_size) / orig_size * 100 if orig_size > 0 else 0
                codec_name = selection_result.best_codec.__class__.__name__.replace('Codec', '')
                transform_name = selection_result.best_transform.name
                
                details = (
                    f"File: {filepath.name}\n"
                    f"Profile: {profile_name}\n"
                    f"Time taken: {elapsed:.2f}s\n\n"
                    f"Original Size: {format_size(orig_size)}\n"
                    f"Compressed Size: {format_size(comp_size)}\n"
                    f"Space Saved: {ratio:.2f}%\n\n"
                    f"--- Strategy Chosen ---\n"
                    f"Transform: {transform_name}\n"
                    f"Codec: {codec_name}\n"
                )
                ResultDialog(self, "Compression Complete", "Archive Successfully Created", details)

            elif msg_type == "extract_ok":
                out_path, orig_size, codec_name, transform_name, elapsed = result
                details = (
                    f"Extracted to: {out_path}\n"
                    f"Restored Size: {format_size(orig_size)}\n"
                    f"Time taken: {elapsed:.2f}s\n\n"
                    f"--- Archive Details ---\n"
                    f"Transform: {transform_name}\n"
                    f"Codec: {codec_name}\n\n"
                    f"Integrity Check: PASS (CRC32 + SHA256)"
                )
                ResultDialog(self, "Extraction Complete", "Archive Verified & Restored", details)

            elif msg_type == "error":
                messagebox.showerror("Error", result)
                
        except queue.Empty:
            self.after(100, self.check_queue)


    def compress_file(self):
        filepath = filedialog.askopenfilename(
            title="Select a file to compress",
            filetypes=[("All Files", "*.*")]
        )
        if not filepath:
            return
            
        filepath = Path(filepath)
        if not filepath.exists():
            messagebox.showerror("Error", "File not found.")
            return
            
        def worker():
            try:
                profile_id = Profile.from_extension(filepath.suffix)
                with open(filepath, 'rb') as f:
                    data = f.read()
                    
                timer = Timer()
                timer.start()
                archive_bytes, selection_result, profile = create_archive(filepath, data, profile_id)
                timer.stop()
                
                downloads_dir = get_downloads_path()
                output_filename = filepath.with_suffix('.zc').name
                out_path = get_safe_output_path(downloads_dir, output_filename)
                
                with open(out_path, 'wb') as f:
                    f.write(archive_bytes)
                    
                orig_size = len(data)
                comp_size = len(archive_bytes)
                profile_name = get_profile_name(profile_id)
                
                self.work_queue.put(("compress_ok", (filepath, out_path, orig_size, comp_size, profile_name, selection_result, timer.elapsed)))
            except Exception as e:
                self.work_queue.put(("error", str(e)))

        self._set_loading_state(True)
        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self.check_queue)
            
            
    def extract_selected(self):
        selected = self.tree.selection()
        if not selected:
            filepath = filedialog.askopenfilename(
                title="Select a .zc archive to decompress",
                filetypes=[("Zero-Compress Archives", "*.zc"), ("All Files", "*.*")]
            )
            if not filepath:
                return
            filepath = Path(filepath)
        else:
            item = self.tree.item(selected[0])
            record_id = item['values'][0]
            records = self.db.get_all_archives()
            target = next((r for r in records if r['id'] == record_id), None)
            if not target:
                return
            filepath = Path(target['file_path'])
            
        if not filepath.exists():
            messagebox.showerror("Error", f"Archive not found: {filepath}")
            return
            
        def worker():
            try:
                with open(filepath, 'rb') as f:
                    archive_data = f.read()
                    
                timer = Timer()
                timer.start()
                orig_name, restored_data, header, v_result = extract_archive(archive_data)
                timer.stop()
                
                downloads_dir = get_downloads_path()
                out_path = get_safe_output_path(downloads_dir, orig_name)
                
                with open(out_path, 'wb') as f:
                    f.write(restored_data)
                    
                from .transforms import get_transform
                from .codecs import get_codec
                
                codec_name = get_codec(header.codec_id).__class__.__name__.replace('Codec', '')
                transform_name = get_transform(header.transform_id).name
                
                self.work_queue.put(("extract_ok", (out_path, len(restored_data), codec_name, transform_name, timer.elapsed)))
            except ArchiveValidationError as e:
                self.work_queue.put(("error", f"Archive rejected! Reason: {e}"))
            except Exception as e:
                self.work_queue.put(("error", str(e)))

        self._set_loading_state(True)
        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self.check_queue)


    def delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
            
        if messagebox.askyesno("Confirm", "Delete selected record from database?"):
            item = self.tree.item(selected[0])
            record_id = item['values'][0]
            self.db.delete_archive(record_id)
            self.refresh_data()

def run_gui():
    app = ZeroShrinkGUI()
    app.mainloop()
