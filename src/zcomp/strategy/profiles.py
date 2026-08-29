class Profile:
    TXT = 1
    PDF = 2
    PNG = 3
    JPEG = 4
    MP4 = 5
    BINARY = 6
    MESH3D = 7
    ANY = 255

    @classmethod
    def from_extension(cls, ext: str) -> int:
        ext_lower = ext.lower()
        if ext_lower == '.txt': return cls.TXT
        if ext_lower == '.pdf': return cls.PDF
        if ext_lower == '.png': return cls.PNG
        if ext_lower in ('.jpg', '.jpeg'): return cls.JPEG
        if ext_lower == '.mp4': return cls.MP4
        if ext_lower == '.bin': return cls.BINARY
        if ext_lower in ('.glb', '.fbx', '.obj', '.stl'): return cls.MESH3D
        return cls.ANY

def get_profile_name(profile_id: int) -> str:
    names = {
        Profile.TXT: "Text Document",
        Profile.PDF: "PDF Document",
        Profile.PNG: "PNG Image",
        Profile.JPEG: "JPEG Image",
        Profile.MP4: "MP4 Video",
        Profile.BINARY: "Structured Binary",
        Profile.MESH3D: "3D Mesh / Model",
        Profile.ANY: "Adaptive Auto-Detect"
    }
    return names.get(profile_id, "Unknown Profile")
