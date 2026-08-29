from .base import BaseTransform
from .identity import IdentityTransform
from .delta import Delta8Transform
from .rle import RleTransform
from .shuffle import Shuffle32Transform, Shuffle64Transform

def get_transform(transform_id: int) -> BaseTransform:
    transforms = {
        0: IdentityTransform,
        1: Delta8Transform,
        2: RleTransform,
        3: Shuffle32Transform,
        4: Shuffle64Transform
    }
    if transform_id not in transforms:
        raise ValueError(f"Unknown transform ID: {transform_id}")
    return transforms[transform_id]()

def get_all_transforms() -> list[BaseTransform]:
    return [
        IdentityTransform(),
        Delta8Transform(),
        RleTransform(),
        Shuffle32Transform(),
        Shuffle64Transform()
    ]

__all__ = [
    "BaseTransform",
    "IdentityTransform",
    "Delta8Transform",
    "RleTransform",
    "Shuffle32Transform",
    "Shuffle64Transform",
    "get_transform",
    "get_all_transforms"
]
