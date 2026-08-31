# zero_shrink1.py - Wrapper pointing to main zero_shrink entry point
import sys
import os

from zero_shrink import ZeroShrinkEngine, ZeroShrinkGUI, HuffmanCoder, Transforms, tk

if __name__ == "__main__":
    root = tk.Tk()
    app = ZeroShrinkGUI(root)
    root.mainloop()
