from .profiles import Profile
from .codecs import get_all_codecs, ZstdCodec, StoreCodec, BaseCodec

def select_best_codec(data: bytes, profile_id: int) -> tuple[BaseCodec, bytes, bytes]:
    """
    Returns (BestCodec, meta, payload)
    """
    if not data:
        store = StoreCodec()
        meta, payload = store.compress(data)
        return store, meta, payload

    candidates = []
    
    if profile_id == Profile.TXT:
        # primary: ZSTD, fallback to Auto
        candidates = get_all_codecs()
    elif profile_id == Profile.PDF:
        # PDF -> ZSTD / LZMA / ZLIB / STORE
        candidates = get_all_codecs()
    elif profile_id in (Profile.PNG, Profile.JPEG, Profile.MP4):
        # Already compressed formats
        candidates = [ZstdCodec(), StoreCodec()]
    else:
        # ANY -> All codecs
        candidates = get_all_codecs()

    best_codec = None
    best_meta = b""
    best_payload = data
    best_size = len(data) + 1 # force store to be evaluated properly
    
    # Evaluate candidates
    for codec in candidates:
        try:
            meta, payload = codec.compress(data)
            total_size = len(meta) + len(payload)
            
            # Deterministic tie break: strictly smaller, or if same size we prefer the first we found (which are ordered by preference)
            if total_size < best_size:
                best_codec = codec
                best_meta = meta
                best_payload = payload
                best_size = total_size
        except Exception:
            # If a codec fails, skip it safely
            continue

    # If no codec made it smaller than original, use STORE
    if best_size >= len(data):
        store = StoreCodec()
        meta, payload = store.compress(data)
        return store, meta, payload
        
    return best_codec, best_meta, best_payload
