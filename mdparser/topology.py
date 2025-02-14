import os
import pathlib
import shlex
import subprocess
import weakref
from collections import OrderedDict
from itertools import islice
from typing import (
    Any,
    Dict,
    List,
    Iterable,
    Iterator,
    Mapping,
    Tuple,
    Type,
    Optional,
    TextIO,
    Union,
)

from ._base import (
    Node,
    NodeValue,
    GenericNodeValue,
    ensure_proxy,
    unproxy_node,
    get_node_path,
)
from . import _gmx_nodes


StrOrPath = Union[str, os.PathLike]


DEFAULT_GENERIC_NODE_VALUE_TYPES = {
    GenericNodeValue._node_key_name: GenericNodeValue,
}

DEFAULT_GMX_NODE_VALUE_TYPES = {}
for name in dir(_gmx_nodes):
    obj = getattr(_gmx_nodes, name)
    if not isinstance(obj, type):
        continue
    if issubclass(obj, NodeValue):
        DEFAULT_GMX_NODE_VALUE_TYPES[obj._node_key_name] = obj


class Topology:
    """Base class for topologies

    Linked list of :class:`Node` instances:
    """

    __node_value_types = DEFAULT_GENERIC_NODE_VALUE_TYPES

    def __init__(self):
        self._nodes = dict()
        self._hardroot = Node()
        self._root = root = weakref.proxy(self._hardroot)
        root.prev = root.next = root

    def __repr__(self):
        return f"{type(self).__name__}()"

    @property
    def node_value_types(self) -> Dict[str, Any]:
        return getattr(self, f"_{type(self).__name__}__node_value_types")

    def __iter__(self) -> Iterator[Node]:
        root = current = self._root
        while current.next is not root:
            current = current.next
            yield current

    def __reversed__(self) -> Iterator[Node]:
        root = current = self._root
        while current.prev is not root:
            current = current.prev
            yield current

    def __len__(self) -> int:
        """Return number of linked nodes"""

        length = 0
        for length, _ in enumerate(self, 1):
            pass

        return length

    def __getitem__(self, query: Union[str, int, slice]) -> Union[Node, Iterator[Node]]:
        def _query_int(query: int) -> Node:
            if not isinstance(query, int):
                raise ValueError(
                    f"items can only be queried by 'str' (node key), "
                    f"or (iterables of) 'int' or 'slice' (node index), "
                    f"not {type(query).__name__!r}"
                )

            if query < 0:
                query = (query * -1) - 1
                iterable = reversed(self)
            else:
                iterable = iter(self)

            try:
                node = next(islice(iterable, query, query + 1))
            except StopIteration:
                raise IndexError("index out of range")
            try:
                node = unproxy_node(node)
            except AttributeError:
                pass
            return node

        if isinstance(query, str):
            return self._nodes[query]

        if isinstance(query, slice):
            return islice(self, query.start, query.stop, query.step)

        if isinstance(query, Iterable):
            return (_query_int(x) for x in query)

        return _query_int(query)

    def __contains__(self, key: str) -> bool:
        if key in self._nodes:
            return True
        return False

    @classmethod
    def select_nvtype(cls, name: str) -> Type[NodeValue]:
        """Retrieve node type by name"""
        return getattr(cls, f"_{cls.__name__}__node_value_types")[name]

    @classmethod
    def make_node_value(
        cls, nvtype: Union[str, Type[NodeValue]], *args: Any, **kwargs: Any
    ) -> Tuple[str, NodeValue]:
        """Initialise node value type and make key

        Args:
            nvtype: Node value type or name
            *args: Passed on to node value type

        Keyword args:
            **kwargs: Passed on to node value type

        Returns:
            A key and initialised node value
        """

        if isinstance(nvtype, str):
            nvtype = cls.select_nvtype(nvtype)

        node_value = nvtype(*args, **kwargs)
        node_key = node_value._make_node_key()

        return node_key, node_value

    def _add_node(self, node: Node, key: Optional[str] = None) -> None:
        if key is None:
            key = node.key

        if key is None:
            raise LookupError(
                "No node key was provided and none could be taken from the node"
            )

        if key in self._nodes:
            raise KeyError(f"node {key!r} does already exist")

        node.key = key
        self._nodes[key] = node

    def _batch_add_nodes(
        self, nodes: Iterable[Node], keys: Optional[Iterable[str]] = None
    ) -> None:
        if keys is None:
            keys = []
            for i, node in enumerate(nodes):
                key = node.key
                if key is None:
                    raise LookupError(
                        f"No node keys were provided and none could be taken from the node with index {i}"
                    )
                keys.append(key)
        else:
            keys = list(keys)

        nodes = list(nodes)

        if len(nodes) != len(keys):
            raise ValueError("Number of nodes and keys must be equal")

        for key in keys:
            if key in self._nodes:
                raise KeyError(f"node {key!r} does already exist")

        for k, node in zip(keys, nodes):
            self._nodes[k] = node

    def add(self, key: str, value: NodeValue) -> None:
        root = self._root
        last = root.prev
        node = Node(key=key, value=value)
        self._add_node(node)
        node.connect(last, forward=False)
        node.connect(root)

    def pop(self, key: str) -> Node:
        node = self._nodes.pop(key)
        node.prev.next = node.next
        node.next.prev = node.prev
        return node

    def discard(self, key: str) -> None:
        try:
            node = self._nodes.pop(key)
        except KeyError:
            pass
        else:
            node.prev.next = node.next
            node.next.prev = node.prev

    def replace(self, key: str, value: NodeValue) -> None:
        """Replace node with specific key while retaining key"""

        old_node = self._nodes.pop(key)
        self._nodes[key] = new_node = Node()
        new_node.key, new_node.value = key, value
        new_node.prev, new_node.next = old_node.prev, old_node.next
        new_node.prev.next = new_node
        new_node.next.prev = weakref.proxy(new_node)

    def index(self, key: str, start: Optional[int] = None, stop: Optional[int] = None):
        """Return index of node

        Args:
            key: Node key
            start: Ignore nodes with lower index
            stop: Ignore nodes with index greater or equal

        Raises:
            ValueError if the key is not present
        """
        if start is None:
            start = AlwaysLess()

        if stop is None:
            stop = AlwaysGreater()

        for i, node in enumerate(self):
            if i < start:
                continue

            if i >= stop:
                break

            if node.key == key:
                return i

        raise ValueError(f"node {key!r} is not in list")

    def insert(self, index: int, key: str, value: NodeValue) -> None:
        """Insert node before index"""

        node = Node(key=key, value=value)
        self._add_node(node)

        prev = root = self._root
        next_node = root.next

        for i, next_node in enumerate(self):
            if i == index:
                prev = next_node.prev
                break
        else:
            prev = root.prev
            next_node = prev.next

        assert prev is not None
        prev.connect(node)
        node.connect(next_node)

    def relative_insert(
        self, node: Node, key: str, value: NodeValue, forward: bool = True
    ) -> None:
        """Insert node after/before other node"""

        new_node = Node(key=key, value=value)
        self._add_node(new_node)

        if forward is True:
            assert node.next is not None
            new_node.connect(node.next)
            new_node.connect(node, forward=False)
        else:
            assert node.prev is not None
            node.prev.connect(new_node)
            new_node.connect(node)

    def block_insert(self, index: int, block_start: Node, block_end: Node) -> None:
        """Insert block of linked nodes before index"""

        if not isinstance(index, int):
            raise ValueError("index must be an integer")

        block_nodes = get_node_path(block_start, block_end)
        self._batch_add_nodes(block_nodes)

        prev = root = self._root
        next_node = root.next

        for i, next_node in enumerate(self):
            if i == index:
                prev = next_node.prev
                break
        else:
            prev = root.prev
            next_node = prev.next

        assert prev is not None
        prev.connect(block_start)
        block_end.connect(next_node)

    def relative_block_insert(
        self, node: Node, block_start: Node, block_end: Node, forward: bool = True
    ):
        """Insert block of linked nodes before/after node"""

        block_nodes = get_node_path(block_start, block_end)
        self._batch_add_nodes(block_nodes)

        if forward is True:
            assert node.next is not None
            block_end.connect(node.next)
            node.connect(block_start)
        else:
            assert node.prev is not None
            node.prev.connect(block_start)
            block_end.connect(node)

    def block_discard(self, block_start: Node, block_end: Node) -> None:
        if not block_start.is_backward_connected:
            raise ValueError("Block start is not backward connected")

        if not block_end.is_forward_connected:
            raise ValueError("Block end is not forward connected")

        prev = block_start.prev
        next_node = block_end.next
        block_start.disconnect(backward=True)
        block_end.disconnect(forward=True)
        prev.connect(next_node)  # type: ignore

        block_nodes = get_node_path(block_start, block_end)
        for node in block_nodes:
            if node.key is not None:
                del self._nodes[node.key]


class GromacsTopology(Topology):
    __node_value_types = {
        **Topology._Topology__node_value_types,
        **DEFAULT_GMX_NODE_VALUE_TYPES,
    }  # type: ignore

    def __str__(self):
        section_type = self.select_nvtype("section")
        entry_type = self.select_nvtype("section_entry")

        return_str = ""
        for node in self:
            if not isinstance(node.value, entry_type) and isinstance(
                node.prev.value, entry_type
            ):
                return_str += "\n"
            elif isinstance(node.value, section_type) and (node.prev is not self._root):
                return_str += "\n"
            return_str += f"{node.value!s}\n"

        return return_str

    @property
    def includes_resolved(self):
        for node in self:
            if isinstance(node.value, self.__node_value_types["include"]):
                return False
        else:
            return True

    @property
    def conditions_resolved(self):
        for node in self:
            if isinstance(node.value, self.__node_value_types["condition"]):
                return False
        else:
            return True

    def find_complement(self, node):
        """Find complementary Condition node"""

        root = self._root

        if node.value.value is None:
            goto = "prev"
        else:
            goto = "next"

        current = getattr(node, goto)
        while current is not root:
            if isinstance(current.value, self.__node_value_types["condition"]):
                if current.value.key == node.value.key:
                    return current
            current = getattr(current, goto)

        return


class GromacsTopologyParser:
    """Read and write GROMACS topology files

    Attributes:
        ignore_comments: If `True`, skips lines starting with ";"
        preprocess: If `True`, runs once through the file before
            actual parsing to resolve includes. Options `include_local`, and
            `include_shared` have no effect if this is `False`.
        include_local: If `True`, tries to resolve "#include" statements
            for local files. Local files are searched for relative to paths
            given in `local_paths`.
        local_paths: List of paths to search for local files. If `None`,
            uses the directory of the file being read, or the current working
            directory if reading string input.
        include_shared: If `True`, tries to resolve "#include" statements
            for shared files. Shared files are searched for relative to paths
            given in `shared_paths`.
        shared_paths: List of paths to search for shared files. If `None`,
            tries to determine the GROMACS shared directory if there is
            a valid installation.
        include_blacklist: List of file paths (local or shared) to exclude from
            inclusion.
        definitions: Mapping of variable names to values. To replicate the
            behaviour of "-DPOSRES" or "#define POSRES", use `{"POSRES": True}`.
        resolve_conditions: If `True`, resolve "#ifdef", "#ifndef", and "#else"
            blocks based on present definitions.
        verbose: Be chatty.
        reset_counts: If `True`, sets the node value type counters to zero before parsing.
    """

    _top_type = GromacsTopology

    def __init__(
        self,
        ignore_comments: bool = True,
        preprocess: bool = True,
        include_local: bool = True,
        include_shared: bool = False,
        local_paths: Optional[Union[StrOrPath, Iterable[StrOrPath]]] = None,
        shared_paths: Optional[Union[StrOrPath, Iterable[StrOrPath]]] = None,
        include_blacklist: Optional[Union[StrOrPath, Iterable[StrOrPath]]] = None,
        definitions: Optional[Mapping[str, Any]] = None,
        resolve_conditions: bool = True,
        verbose: bool = True,
        reset_counts: bool = True,
    ):
        self.ignore_comments = ignore_comments
        self.preprocess = preprocess
        self.include_local = include_local
        self.local_paths = self.to_list_of_paths(local_paths)
        self.include_shared = include_shared
        self.shared_paths = self.to_list_of_paths(shared_paths)
        self.include_blacklist = self.to_list_of_paths(include_blacklist, resolve=False)
        self.resolve_conditions = resolve_conditions
        self.verbose = verbose
        self.reset_counts = reset_counts

        if definitions is None:
            definitions = {}
        self.definitions = {**definitions}

    @staticmethod
    def to_list_of_paths(
        paths: Optional[Union[StrOrPath, Iterable[StrOrPath]]], resolve: bool = True
    ) -> Optional[List[pathlib.Path]]:
        """Convert input to list of pathlib.Path instances"""

        if paths is None:
            return

        if isinstance(paths, str) or not isinstance(paths, Iterable):
            paths = [paths]

        if resolve:
            return [pathlib.Path(f).resolve() for f in paths]

        return [pathlib.Path(f) for f in paths]

    def preprocess_includes(
        self,
        file: Union[TextIO, Iterable[str]],
        local_paths: Optional[List[pathlib.Path]] = None,
        shared_paths: Optional[List[pathlib.Path]] = None,
        include_blacklist: Optional[List[pathlib.Path]] = None,
    ) -> Iterator[str]:
        """Pre-process topology file-like object

        Yield topology file line by line and resolve '#include'
        statements.
        """

        if local_paths is None:
            _local_paths = []

            try:
                file_path = pathlib.Path(file.name).parent.absolute()
            except AttributeError:
                file_path = pathlib.Path.cwd()
            _local_paths.append(file_path)

        if shared_paths is None:
            shared_paths = []

            gmx_shared = get_gmx_dir()[1]
            if gmx_shared is not None:
                shared_paths.append(gmx_shared)

        if include_blacklist is None:
            include_blacklist = []

        for line in file:
            if not line.startswith("#include"):
                yield line
                continue

            include_file = line.split()[1].strip('"')
            excluded = False

            found_locally = False
            if self.include_local:
                for include_dir in _local_paths:
                    include_path = include_dir / include_file

                    if not include_path.is_file():
                        continue

                    if path_in_paths(include_path, include_blacklist):
                        excluded = True
                        if self.verbose:
                            print(f"Not including {include_path} (blacklist)")
                        continue

                    with open(include_path) as fp:
                        if self.verbose:
                            print(f"Including {include_path} (local)")

                        yield from self.preprocess_includes(
                            fp,
                            local_paths=local_paths,
                            shared_paths=shared_paths,
                            include_blacklist=include_blacklist,
                        )
                    found_locally = True
                    break

            found_shared = False
            if not found_locally and self.include_shared:
                for include_dir in shared_paths:
                    include_path = include_dir / include_file

                    if not include_path.is_file():
                        continue

                    if path_in_paths(include_path, include_blacklist):
                        excluded = True
                        if self.verbose:
                            print(f"Not including {include_path} (blacklist)")
                        continue

                    with open(include_path) as open_file:
                        if self.verbose:
                            print(f"Including {include_path} (shared)")

                        yield from self.preprocess_includes(
                            open_file,
                            local_paths=local_paths,
                            shared_paths=shared_paths,
                            include_blacklist=include_blacklist,
                        )
                    found_shared = True
                    break

            if not (found_locally or found_shared):
                if self.verbose & (not excluded):
                    print(f"Could not find {include_file}")
                yield line

    def read(self, file: Union[TextIO, Iterable[str]]) -> GromacsTopology:
        top = self._top_type()

        if self.preprocess:
            file = self.preprocess_includes(
                file,
                local_paths=self.local_paths,
                shared_paths=self.shared_paths,
                include_blacklist=self.include_blacklist,
            )

        active_section = None
        active_supersection = None
        active_category = 0  # 0: header, 1: moleculetype sections, 2: system sections

        active_conditions = OrderedDict()
        active_definitions = {}
        active_definitions.update(self.definitions)

        if self.reset_counts:
            for node_value_type in top.node_value_types.values():
                node_value_type.reset_count()

        previous = ""
        for line in file:
            if line.strip().endswith("\\"):
                # Resolve multi-line statement
                line = line[: line.rfind("\\")]
                previous = f"{previous}{line}"
                continue

            line = f"{previous}{line}"
            previous = ""

            if self.ignore_comments:
                line, _ = split_comment(line)

            line = line.strip()

            if line in ["", "\n", "\n\r"]:
                continue

            if line.startswith("#define"):
                line = line.lstrip("#define").lstrip().split(maxsplit=1)
                if len(line) == 1:
                    node_key, node_value = top.make_node_value("define", line[0], True)
                    top.add(node_key, node_value)
                    active_definitions[line[0]] = True
                else:
                    node_key, node_value = top.make_node_value(
                        "define", line[0], line[1]
                    )
                    top.add(node_key, node_value)
                    active_definitions[line[0]] = line[1]
                continue

            if line.startswith("#undef"):
                line = line.lstrip("#undef").lstrip()
                node_key, node_value = top.make_node_value("define", line, False)
                top.add(node_key, node_value)
                _ = active_definitions.pop(line)
                continue

            if line.startswith("#ifdef"):
                line = line.lstrip("#ifdef").lstrip()
                active_conditions[line] = True
                if not self.resolve_conditions:
                    node_key, node_value = top.make_node_value("condition", line, True)
                    top.add(node_key, node_value)
                continue

            if line.startswith("#ifndef"):
                line = line.lstrip("#ifndef").lstrip()
                active_conditions[line] = False
                if not self.resolve_conditions:
                    node_key, node_value = top.make_node_value("condition", line, False)
                    top.add(node_key, node_value)
                continue

            if line.startswith("#else"):
                last_condition, last_value = next(reversed(active_conditions.items()))
                active_conditions[last_condition] = not last_value

                if not self.resolve_conditions:
                    node_key, node_value = top.make_node_value(
                        "condition", last_condition, None
                    )
                    top.add(node_key, node_value)

                    node_key, node_value = top.make_node_value(
                        "condition", last_condition, not last_value
                    )
                    top.add(node_key, node_value)
                    continue

            if line.startswith("#endif"):
                last_condition, _ = active_conditions.popitem(last=True)
                if not self.resolve_conditions:
                    node_key, node_value = top.make_node_value(
                        "condition", last_condition, None
                    )
                    top.add(node_key, node_value)

                    node = top[-1]
                    complement = top.find_complement(node)
                    if complement is not None:
                        node.value.complement = ensure_proxy(complement)
                        complement.value.complement = ensure_proxy(node)

                continue

            if self.resolve_conditions:
                skip = False
                for condition, required_value in active_conditions.items():
                    defined_value = active_definitions.get(condition, False)
                    if defined_value:
                        # Something truthy?
                        defined_value = True
                    if defined_value is not required_value:
                        skip = True
                        break

                if skip:
                    continue

            if line.startswith(";"):
                comment = line[1:].strip()
                node_key, node_value = top.make_node_value("comment", comment)
                top.add(node_key, node_value)
                continue

            if line.startswith("#include"):
                include = line.strip("#include").lstrip()
                node_key, node_value = top.make_node_value("include", include)
                top.add(node_key, node_value)
                continue

            if line.startswith("["):
                _new_section = line.strip(" []").casefold()
                nvtype = top.node_value_types.get(_new_section, None)
                if nvtype is None:
                    # Should not happen for compliant topologies
                    if self.verbose:
                        print(f"Unknown section {_new_section}")

                    node_key, node_value = top.make_node_value("section", _new_section)
                    top.add(node_key, node_value)
                    active_section = active_supersection = node_value
                    continue

                if (nvtype.category < active_category) and self.verbose:
                    print(f"Inconsistent section {_new_section}")
                else:
                    active_category = nvtype.category

                issubsection = issubclass(nvtype, top.node_value_types["subsection"])

                if issubsection:
                    node_value = nvtype(section=weakref.proxy(active_supersection))
                    active_section = node_value
                else:
                    node_value = nvtype()
                    active_section = active_supersection = node_value

                node_key = node_value._make_node_key()
                top.add(node_key, node_value)
                continue

            if active_section is None:
                node_key, node_value = top.make_node_value("comment", line)
                node_value._char = None  # type:ignore
                top.add(node_key, node_value)
                continue

            expected_entry = f"{active_section._node_key_name}_entry"
            nvtype = top.node_value_types.get(expected_entry, False)
            if nvtype is not False:
                if not self.ignore_comments:
                    line, comment = split_comment(line)
                else:
                    comment = None

                args = line.split()

                try:
                    node_value = nvtype.from_line(*args, comment=comment)
                except TypeError:
                    # Should not happen if entry type can deal with line
                    if comment is not None:
                        line += f" ; {comment}"
                    node_value = nvtype.create_raw(f"{line}")
                finally:
                    node_key = node_value._make_node_key()

                top.add(node_key, node_value)
                continue

            # Absolute fallback
            node_key, node_value = top.make_node_value("generic", line)
            top.add(node_key, node_value)

        return top


class AlwaysGreater:
    __slots__ = []

    def __eq__(self, other):
        return False

    def __gt__(self, other):
        return True

    def __ge__(self, other):
        return True

    def __lt__(self, other):
        return False

    def __le__(self, other):
        return False


class AlwaysLess:
    __slots__ = []

    def __eq__(self, other):
        return False

    def __gt__(self, other):
        return False

    def __ge__(self, other):
        return False

    def __lt__(self, other):
        return True

    def __le__(self, other):
        return True


def get_gmx_dir():
    """Find absolute location of the gromacs shared library files

    This function uses a quick and dirty approach: GROMACS is called and
    stdout is parsed for the entries 'Executable' and 'Data prefix'.
    """

    call = "gmx -h"
    try:
        feedback = subprocess.run(
            shlex.split(call),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding="utf8",
        )
    except FileNotFoundError:
        return None, None

    if feedback.returncode != 0:
        return None, None

    _feedback = feedback.stderr.split("\n")

    gmx_exe = None
    gmx_shared = None

    for line in _feedback:
        if line.startswith("Executable"):
            gmx_exe = pathlib.Path(line.split()[-1])
        if line.startswith("Data prefix"):
            gmx_shared = pathlib.Path(line.split()[-1]) / "share/gromacs/top"

    return gmx_exe, gmx_shared


def split_comment(line):
    if ";" in line:
        return tuple(line.split(";", maxsplit=1))
    return line, None


def path_in_paths(test_path: pathlib.Path, path_list: List[pathlib.Path]) -> bool:
    for compare in path_list:
        compare_parts = compare.parts
        if test_path.parts[-len(compare_parts) :] == compare_parts:
            return True

    return False
