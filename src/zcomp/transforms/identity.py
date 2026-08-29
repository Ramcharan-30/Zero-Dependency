from .base import BaseTransform

class IdentityTransform(BaseTransform):
    @property
    def transform_id(self) -> int:
        return 0

    @property
    def name(self) -> str:
        return "NONE"

    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        return b"", data

    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        return transformed_data
