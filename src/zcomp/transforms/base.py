from abc import ABC, abstractmethod

class BaseTransform(ABC):
    @property
    @abstractmethod
    def transform_id(self) -> int:
        """Unique integer identifier for the transform."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Human readable name of the transform."""
        pass

    @abstractmethod
    def transform(self, data: bytes) -> tuple[bytes, bytes]:
        """
        Transforms input bytes into (transform_metadata, transformed_bytes).
        """
        pass

    @abstractmethod
    def inverse(self, meta: bytes, transformed_data: bytes) -> bytes:
        """
        Reverses the transform given the metadata and transformed bytes to recover exact original bytes.
        """
        pass
