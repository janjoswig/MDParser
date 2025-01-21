from abc import ABC, abstractmethod
from typing import Optional


def trim_locals(d):
    return {k: v for k, v in d.items() if k not in ("self", "__class__")}


def make_formatter(f):
    def formatter(value):
        return f"{value:{f}}"

    return formatter


class NodeValue(ABC):
    """Abstract base class for node value types"""

    _count = 0
    _node_key_name = "abstract"

    @classmethod
    def reset_count(cls, value: Optional[int] = None):
        if value is None:
            value = 0
        cls._count = value

    @classmethod
    def increase_count(cls):
        cls._count += 1

    @property
    def count(self):
        return self._count

    def __init__(self):
        self.increase_count()
        self._count = type(self)._count

    @abstractmethod
    def __str__(self):
        """Return node content formatted for topology file"""

    def __repr__(self):
        """Default representation"""
        return f"{type(self).__name__}()"

    def _make_node_key(self) -> str:
        """Return string usable as node key"""
        return f"{self._node_key_name}_{self._count}"


class GenericNodeValue(NodeValue):
    """Generic fallback node value"""

    _node_key_name = "generic"

    def __init__(self, value):
        super().__init__()
        self.value = value

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value!r})"
