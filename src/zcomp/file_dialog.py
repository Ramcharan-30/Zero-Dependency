import tkinter as tk
from tkinter import filedialog
from pathlib import Path
from typing import Optional

def select_file(operation: str) -> Optional[Path]:
    """Open a native file dialog to select a file."""
    root = tk.Tk()
    root.withdraw() # Hide the main window
    
    # Keep window on top
    root.attributes('-topmost', True)
    
    if operation == "compress":
        title = "Select a file to compress"
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
