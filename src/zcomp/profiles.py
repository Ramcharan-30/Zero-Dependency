class Profile:
    TXT = 1
    PDF = 2
    PNG = 3
    JPEG = 4
    MP4 = 5
    ANY = 255

    @classmethod
    def from_extension(cls, ext: str) -> int:
        ext = ext.lower()
        if ext == '.txt': return cls.TXT
        if ext == '.pdf': return cls.PDF
        if ext == '.png': return cls.PNG
        if ext in ('.jpg', '.jpeg'): return cls.JPEG
        if ext == '.mp4': return cls.MP4
        return cls.ANY
