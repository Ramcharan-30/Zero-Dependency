import math
from collections import Counter

def calculate_entropy(data: bytes) -> float:
    """
    Calculates the Shannon entropy of the given byte data in bits per byte.
    Result ranges from 0.0 (all bytes identical) to 8.0 (completely uniform/random bytes).
    """
    if not data:
        return 0.0
    
    length = len(data)
    counts = Counter(data)
    entropy = 0.0
    
    for count in counts.values():
        p = count / length
        entropy -= p * math.log2(p)
        
    return entropy
