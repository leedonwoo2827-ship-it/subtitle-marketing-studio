"""Studio registry public API."""
from studio.registry import REGISTRY


def list_studios():
    return sorted(REGISTRY, key=lambda s: s.order)


def get_studio(key: str):
    for s in REGISTRY:
        if s.key == key:
            return s
    raise KeyError(f"Studio '{key}' not registered")


def sections():
    seen: dict[str, list] = {}
    for s in list_studios():
        seen.setdefault(s.section, []).append(s)
    return seen
