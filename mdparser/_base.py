import weakref
from abc import ABC, abstractmethod
from collections import OrderedDict
from copy import copy
from typing import Any, Callable, List, Optional


def trim_locals(d):
    return {k: v for k, v in d.items() if k not in ("self", "__class__")}


def make_formatter(f: Optional[str] = None) -> Callable[[Any], str]:
    def formatter(value):
        if f is None:
            return f"{value}"
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


class RootNodeValue(NodeValue):
    """Sentinel value for root nodes"""

    _node_key_name = "root"

    def __str__(self) -> str:
        return __repr__()

    def __repr__(self):
        return f"{type(self).__name__}"


class Node:
    __slots__ = ["_prev", "_next", "_key", "value", "__weakref__"]

    def __init__(
        self,
        *,
        key: Optional[str] = None,
        value: Optional[Any] = None,
        prev: Optional["Node"] = None,
        next: Optional["Node"] = None,
    ) -> None:
        self.key = key
        self.value = value
        self.prev = prev
        self.next = next

    def __copy__(self):
        return Node(key=self.key, value=self.value, prev=self.prev, next=self.next)

    @property
    def key(self) -> Optional[str]:
        if self._key is not None:
            return self._key

        if self.value is not None:
            try:
                self._key = self.value._make_node_key()
            except AttributeError:
                pass

        return self._key

    @key.setter
    def key(self, value: Optional[str]) -> None:
        self._key = value

    @property
    def prev(self) -> Optional["Node"]:
        return self._prev

    @prev.setter
    def prev(self, value: Optional["Node"]) -> None:
        if value is not None:
            value = ensure_proxy(value)
        self._prev = value

    @property
    def next(self) -> Optional["Node"]:
        return self._next

    @next.setter
    def next(self, value: Optional["Node"]) -> None:
        self._next = value

    def __repr__(self) -> str:
        attr_str = f"(key={self.key!r}, value={self.value!r})"
        return f"{type(self).__name__}{attr_str}"

    def connect(self, other: "Node", forward: bool = True) -> None:
        """Link another node in forward/backward direction

        Note:
            Does not attempt to unproxy nodes, so it is recommended
            to call `connect` in forward direction only passing unproxied nodes
            or in backward direction only from unproxied nodes.

        Args:
            other: Node to connect to

        Keyword args:
            forward: If `True`, connect to `other` as next node. Otherwise,
                connect to `other` as previous node.
        """

        if forward is True:
            self.next = other
            other.prev = ensure_proxy(self)
        else:
            self.prev = ensure_proxy(other)
            other.next = self

    def disconnect(self, forward: bool = False, backward: bool = False) -> None:
        if backward:
            self.prev.next = None
            self.prev = None

        if forward:
            self.next.prev = None
            self.next = None

    @property
    def is_connected(self) -> bool:
        return self.is_forward_connected and self.is_backward_connected

    @property
    def is_forward_connected(self) -> bool:
        return self.next is not None

    @property
    def is_backward_connected(self) -> bool:
        return self.prev is not None


def ensure_proxy(obj):
    """Return a proxy of an object avoiding proxy of proxy"""

    if not isinstance(obj, (weakref.ProxyType, weakref.CallableProxyType)):
        return weakref.proxy(obj)

    return obj


def unproxy_node(node) -> Node:
    return node.prev.next


def get_node_path(start: Node, end: Node):
    if start is end:
        return [start]

    seen_nodes = OrderedDict()
    seen_nodes[start] = None
    reached_end = False
    while not reached_end and start.is_forward_connected:
        start = start.next  # type: ignore
        if start in seen_nodes:
            raise ValueError("Could not reach end node")
        seen_nodes[start] = None
        reached_end = start is end

    if reached_end:
        return list(seen_nodes.keys())

    raise ValueError("Could not reach end node")


def copy_nodes(nodes: List[Node]) -> List[Node]:
    last_node = copy(nodes[0])
    nodes_copy = [last_node]
    for node in nodes[1:]:
        node = copy(node)
        nodes_copy.append(node)
        last_node.connect(node)
        last_node = node

    return nodes_copy
