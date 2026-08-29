from pathlib import Path
from .profiles import Profile

def validate_selection(filepath: Path, expected_profile: int) -> bool:
    if expected_profile == Profile.ANY:
        return True
        
    ext = filepath.suffix.lower()
    
    if expected_profile == Profile.TXT and ext != '.txt': return False
    if expected_profile == Profile.PDF and ext != '.pdf': return False
    if expected_profile == Profile.PNG and ext != '.png': return False
    if expected_profile == Profile.JPEG and ext not in ('.jpg', '.jpeg'): return False
    if expected_profile == Profile.MP4 and ext != '.mp4': return False
    
    return True

def get_profile_name(profile_id: int) -> str:
    names = {
        Profile.TXT: "Text (.txt)",
        Profile.PDF: "PDF (.pdf)",
        Profile.PNG: "PNG (.png)",
        Profile.JPEG: "JPEG (.jpg/.jpeg)",
        Profile.MP4: "MP4 (.mp4)",
        Profile.ANY: "Any File Type"
    }
    return names.get(profile_id, "Unknown")
