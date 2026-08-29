"""
Zero-Compress - Lossless File Tool
"""
import sys

def main():
    try:
        from src.zcomp.gui import run_gui
        run_gui()
    except ImportError as e:
        print(f"Failed to load GUI (Tkinter might be missing): {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
