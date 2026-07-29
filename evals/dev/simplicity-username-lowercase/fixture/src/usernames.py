"""Username helpers and a separately used generic policy."""


class NormalizationPolicy:
    """A generic transform pipeline used by import tooling."""

    def __init__(self, transforms):
        self.transforms = tuple(transforms)

    def apply(self, value):
        for transform in self.transforms:
            value = transform(value)
        return value


def normalize_username(value):
    return value.strip()
