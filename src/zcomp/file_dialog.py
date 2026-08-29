import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional
from .profiles import Profile

def select_file(operation: str, profile_id: int = Profile.ANY) -> Optional[Path]:
    root = tk.Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    
    if operation == "compress":
        title = "Select a file to compress"
        if profile_id == Profile.TXT:
            filetypes = [("Text files", "*.txt"), ("All Files", "*.*")]
        elif profile_id == Profile.PDF:
            filetypes = [("PDF files", "*.pdf"), ("All Files", "*.*")]
        elif profile_id == Profile.PNG:
            filetypes = [("PNG images", "*.png"), ("All Files", "*.*")]
        elif profile_id == Profile.JPEG:
            filetypes = [("JPEG images", "*.jpg *.jpeg"), ("All Files", "*.*")]
        elif profile_id == Profile.MP4:
            filetypes = [("MP4 video", "*.mp4"), ("All Files", "*.*")]
        else:
            filetypes = [("All Files", "*.*")]
    elif operation == "decompress":
        title = "Select a .zc archive to decompress"
        filetypes = [("Zero-Compress Archives", "*.zc"), ("All Files", "*.*")]
    else:
        title = "Select a file"
        filetypes = [("All Files", "*.*")]
        
    filepath = filedialog.askopenfilename(
        title=title,
        filetypes=filetypes
    )
    
    root.destroy()
    
    if filepath:
        return Path(filepath)
    return None
