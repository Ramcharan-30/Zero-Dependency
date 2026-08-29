import os
from pathlib import Path

def get_downloads_path() -> Path:
    """Return the path to the user's Downloads directory."""
    if os.name == 'nt':
        import winreg
        try:
            sub_key = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
                downloads_path = winreg.QueryValueEx(key, "{374DE290-123F-4565-9164-39C4925E467B}")[0]
                return Path(downloads_path)
        except Exception:
            return Path.home() / "Downloads"
    else:
        return Path.home() / "Downloads"

def get_safe_output_path(downloads_dir: Path, filename: str) -> Path:
    """Generate a collision-safe output path in the given directory."""
    # Ensure filename is safe (no path traversal)
    safe_name = Path(filename).name
    base_path = downloads_dir / safe_name
    if not base_path.exists():
        return base_path
    
    name = base_path.stem
    ext = base_path.suffix
    counter = 1
    
    while True:
        new_path = downloads_dir / f"{name} ({counter}){ext}"
        if not new_path.exists():
            return new_path
        counter += 1
