from .base import BaseTransform

class MeshTransform(BaseTransform):
    @property
    def transform_id(self) -> int:
        return 5

    @property
    def name(self) -> str:
        return "Mesh3D_Transform"

    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        if not data:
            return b'\x00', b''
            
        rem = len(data) % 12
        padded = data if rem == 0 else data + b'\x00' * (12 - rem)
        
        out = bytearray(len(padded))
        L = len(padded) // 12
        
        # 12 byte planes (e.g. X1X2X3X4 Y1Y2Y3Y4 Z1Z2Z3Z4)
        for i in range(L):
            idx = i * 12
            for p in range(12):
                out[p*L + i] = padded[idx + p]
                
        # Apply 1D delta on the shuffled data for Draco-like spatial compression
        delta_out = bytearray(len(out))
        if len(out) > 0:
            delta_out[0] = out[0]
            for i in range(1, len(out)):
                delta_out[i] = (out[i] - out[i-1]) % 256
                
        return bytes([rem]), bytes(delta_out)

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        if not transformed_data:
            return b''
            
        rem = meta[0]
        
        # Undo delta
        out = bytearray(len(transformed_data))
        out[0] = transformed_data[0]
        for i in range(1, len(transformed_data)):
            out[i] = (out[i-1] + transformed_data[i]) % 256
            
        # Undo shuffle
        unshuffled = bytearray(len(out))
        L = len(out) // 12
        for i in range(L):
            idx = i * 12
            for p in range(12):
                unshuffled[idx + p] = out[p*L + i]
                
        if rem != 0:
            return bytes(unshuffled[:-(12 - rem)])
        return bytes(unshuffled)
