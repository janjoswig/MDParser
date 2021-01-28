from collections import OrderedDict
from itertools import islice
import pathlib
import shlex
import subprocess
from typing import Any, Iterable, Mapping, Optional, TextIO, Union
import weakref

from . import _gmx_nodes


DEFAULT_NODE_VALUE_TYPES = {
        "generic": _gmx_nodes.GenericNodeValue,
        "comment": _gmx_nodes.Comment,
        "define": _gmx_nodes.Define,
        "include": _gmx_nodes.Include,
        "condition": _gmx_nodes.Condition,
        "section": _gmx_nodes.Section,
        "defaults": _gmx_nodes.DefaultsSection,
        "atomtypes": _gmx_nodes.AtomtypesSection,
        "bondtypes": _gmx_nodes.BondtypesSection,
        "angletypes": _gmx_nodes.AngletypesSection,
        "pairtypes": _gmx_nodes.PairtypesSection,
        "dihedraltypes": _gmx_nodes.DihedraltypesSection,
        "constrainttypes": _gmx_nodes.ConstrainttypesSection,
        "nonbonded_params": _gmx_nodes.NonbondedParamsSection,
        "moleculetype": _gmx_nodes.MoleculetypeSection,
        "system": _gmx_nodes.SystemSection,
        "molecules": _gmx_nodes.MoleculesSection,
        "subsection": _gmx_nodes.Subsection,
        "atoms": _gmx_nodes.AtomsSubsection,
        "bonds": _gmx_nodes.BondsSubsection,
        "pairs": _gmx_nodes.PairsSubsection,
        "pairs_nb": _gmx_nodes.PairsNBSubsection,
        "angles": _gmx_nodes.AnglesSubsection,
        "dihedrals": _gmx_nodes.DihedralsSubsection,
        "exclusions": _gmx_nodes.ExclusionsSubsection,
        "constraints": _gmx_nodes.ConstraintsSubsection,
        "settles": _gmx_nodes.SettlesSubsection,
        "virtual_sites2": _gmx_nodes.VirtualSites2Subsection,
        "virtual_sites3": _gmx_nodes.VirtualSites3Subsection,
        "virtual_sites4": _gmx_nodes.VirtualSites4Subsection,
        "virtual_sitesn": _gmx_nodes.VirtualSitesNSubsection,
        "position_restraints": _gmx_nodes.PositionRestraintsSubsection,
        "distance_restraints": _gmx_nodes.DistanceRestraintsSubsection,
        "dihedral_restraints": _gmx_nodes.DihedralRestraintsSubsection,
        "orientation_restraints": _gmx_nodes.OrientationRestraintsSubsection,
        "angle_restraints": _gmx_nodes.AngleRestraintsSubsection,
        "angle_restraints_z": _gmx_nodes.AngleRestraintsZSubsection,
        "defaults_entry": _gmx_nodes.DefaultsEntry,
    }


class GromacsTop:

    __node_value_types = DEFAULT_NODE_VALUE_TYPES

    def __init__(self):
        self._nodes = dict()
        self._hardroot = Node()
        self._hardroot.key = self._hardroot.value = None
        self._root = root = weakref.proxy(self._hardroot)
        root.prev = root.next = root

    def __str__(self):
        return_str = ""
        for node in self:
            return_str += f"{node.key:<20} {node.value!s}\n\n"

        return return_str

    def __repr__(self):
        return f"{type(self).__name__}()"

    def __iter__(self):
        root = current = self._root
        while current.next is not root:
            current = current.next
            yield current

    def __reversed__(self):
        root = current = self._root
        while current.prev is not root:
            current = current.prev
            yield current

    def __len__(self):
        """Return number of nodes (may happen to be not all connected)"""
        return self._nodes.__len__()

    def __getitem__(self, query):
        if isinstance(query, str):
            return self._nodes.__getitem__(query)

        if isinstance(query, slice):
            return islice(self, query.start, query.stop, query.step)

        if isinstance(query, int):
            if query < 0:
                query = (query * -1) - 1
                iterable = reversed(self)
            else:
                iterable = iter(self)

            try:
                return next(islice(iterable, query, query + 1))
            except StopIteration:
                raise IndexError("index out of range")

        raise ValueError(
            f"items should be queried by 'str' (node key), "
            f"or 'int' or 'slice' (node index), not {type(query).__name__!r}"
            )

    def __contains__(self, key):
        if key in self._nodes:
            return True
        return False

    def _check_key_and_add_new_node(self, key):
        if key in self._nodes:
            raise KeyError(f"node {key!r} does already exist")

        self._nodes[key] = node = Node()

        return node

    def add(self, key, value) -> None:

        node = self._check_key_and_add_new_node(key)

        root = self._root
        last = root.prev
        node.prev, node.next, node.key, node.value = last, root, key, value
        last.next = node
        root.prev = weakref.proxy(node)

    def discard(self, key) -> None:
        try:
            node = self._nodes.pop(key)
        except KeyError:
            pass
        else:
            node.prev.next = node.next
            node.next.prev = node.prev

    def replace(self, key, value):
        """Replace node with specific key while retaining key"""

        old_node = self._nodes.pop(key)
        self._nodes[key] = new_node = Node()
        new_node.key, new_node.value = key, value
        new_node.prev, new_node.next = old_node.prev, old_node.next
        new_node.prev.next = new_node
        new_node.next.prev = weakref.proxy(new_node)

    def index(self, key, start=None, stop=None):
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
            stop = AlwayGreater()

        for i, node in enumerate(self):
            if i < start:
                continue

            if i >= stop:
                break

            if node.key == key:
                return i

        raise ValueError(f"node {key!r} is not in list")

    def insert(self, index, key, value):
        """Insert node before index"""

        node = self._check_key_and_add_new_node(key)
        prev = root = self._root
        next_node = root.next

        for i, next_node in enumerate(self):
            if i == index:
                prev = next_node.prev
                break
        else:
            prev = root.prev
            next_node = prev.next

        node.prev, node.next = prev, next_node
        node.key, node.value = key, value
        prev.next = node
        next_node.prev = weakref.proxy(node)

    @property
    def includes_resolved(self):
        for node in self:
            if isinstance(node.value, _gmx_nodes.Include):
                return False
        else:
            return True

    @property
    def conditions_resolved(self):
        for node in self:
            if isinstance(node.value, _gmx_nodes.Condition):
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
            if isinstance(current.value, _gmx_nodes.Condition):
                if current.value.key == node.value.key:
                    return current
            current = getattr(current, goto)

        return


class GromacsTopParser:
    """Read and write GROMACS topology files"""

    __node_value_types = DEFAULT_NODE_VALUE_TYPES

    def __init__(
            self,
            ignore_comments: bool = True,
            comment_chars: Optional[Iterable[str]] = None,
            preprocess: bool = True,
            include_local: bool = True,
            include_shared: bool = False,
            local_paths: Optional[Iterable[Any]] = None,
            shared_paths: Optional[Iterable[Any]] = None,
            definitions: Optional[Mapping[str, Any]] = None,
            resolve_conditions: bool = True,
            verbose: bool = True):

        self.ignore_comments = ignore_comments

        if comment_chars is None:
            comment_chars = [";", "*"]
        self.comment_chars = [char for char in comment_chars]

        self.preprocess = preprocess
        self.include_local = include_local

        if local_paths is not None:
            local_paths = [pathlib.Path(p) for p in local_paths]
        self.local_paths = local_paths

        self.include_shared = include_shared

        if shared_paths is not None:
            shared_paths = [pathlib.Path(p) for p in shared_paths]
        self.shared_paths = shared_paths

        self.verbose = verbose
        self.resolve_conditions = resolve_conditions

        self.definitions = {}
        if definitions is not None:
            self.definitions.update(definitions)

    def preprocess_includes(
            self,
            file: Union[TextIO, Iterable[str]],
            include_local=True,
            local_paths=None,
            include_shared=False,
            shared_paths=None):
        """Pre-process topology file-like object

        Yield topology file line by line and resolve '#include'
        statements.

        Args:
            file: File-like iterable.
        """

        if local_paths is None:
            _local_paths = []

            try:
                file_path = pathlib.Path(file.name).parent.absolute()
            except AttributeError:
                file_path = None

            if file_path is not None:
                _local_paths.append(file_path)

        else:
            _local_paths = [pathlib.Path(p) for p in local_paths]

        if shared_paths is None:
            shared_paths = []
            gmx_shared = get_gmx_dir()[1]
            if gmx_shared is not None:
                shared_paths.append(gmx_shared)

        else:
            shared_paths = [pathlib.Path(p) for p in shared_paths]

        for line in file:
            if not line.startswith('#include'):
                yield line
                continue

            include_file = line.split()[1].strip('"')

            found_locally = False
            if include_local:
                for include_dir in _local_paths:
                    include_path = include_dir / include_file
                    if not include_path.is_file():
                        continue

                    with open(include_path) as open_file:
                        yield from self.preprocess_includes(
                            open_file,
                            include_local=include_local,
                            local_paths=local_paths,
                            include_shared=include_shared,
                            shared_paths=shared_paths
                        )
                    found_locally = True
                    break

            found_shared = False
            if not found_locally and include_shared:
                for include_dir in shared_paths:
                    include_path = include_dir / include_file
                    if not include_path.is_file():
                        continue

                    with open(include_path) as open_file:
                        yield from self.preprocess_includes(
                            open_file,
                            include_local=include_local,
                            local_paths=local_paths,
                            include_shared=include_shared,
                            shared_paths=shared_paths
                        )
                    found_shared = True
                    break

            if not (found_locally or found_shared):
                yield line

    def read(self, file: Iterable) -> GromacsTop:
        top = GromacsTop()

        if self.preprocess:
            file = self.preprocess_includes(
                file,
                include_local=self.include_local,
                local_paths=self.local_paths,
                include_shared=self.include_shared,
                shared_paths=self.shared_paths
                )

        comment_chars = tuple(self.comment_chars)

        active_section = None
        active_category = 0

        active_conditions = OrderedDict()
        active_definitions = {}
        active_definitions.update(self.definitions)

        for node_value_type in self.__node_value_types.values():
            node_value_type.reset_count()

        previous = ''
        for line in file:

            if line.strip().endswith('\\'):
                # Resolve multi-line statement
                line = line[:line.rfind('\\')]
                previous = f"{previous}{line}"
                continue

            line = f"{previous}{line}"
            previous = ''

            line = line.strip()

            if self.ignore_comments:
                for char in comment_chars:
                    if char not in line:
                        continue

                    line = line[:line.index(char)].strip()

            if line in ['', '\n', '\n\r']:
                continue

            if line.startswith('#define'):
                line = line.lstrip("#define").lstrip().split(maxsplit=1)
                if len(line) == 1:
                    node_key, node_value = self._select_node_type(
                        "define", line[0], True
                    )
                    top.add(node_key, node_value)
                    active_definitions[line[0]] = True
                else:
                    node_key, node_value = self._select_node_type(
                        "define", line[0], line[1]
                    )
                    top.add(node_key, node_value)
                    active_definitions[line[0]] = line[1]
                continue

            if line.startswith('#undef'):
                line = line.lstrip("#undef").lstrip()
                node_key, node_value = self._select_node_type(
                    "define", line, False
                )
                top.add(node_key, node_value)
                _ = active_definitions.pop(line)
                continue

            if line.startswith('#ifdef'):
                line = line.lstrip('#ifdef').lstrip()
                active_conditions[line] = True
                if not self.resolve_conditions:
                    node_key, node_value = self._select_node_type(
                        "condition", line, True
                    )
                    top.add(node_key, node_value)
                continue

            if line.startswith('#ifndef'):
                line = line.lstrip('#ifndef').lstrip()
                active_conditions[line] = False
                if not self.resolve_conditions:
                    node_key, node_value = self._select_node_type(
                        "condition", line, False
                    )
                    top.add(node_key, node_value)
                continue

            if line.startswith('#else'):
                last_condition, last_value = next(
                    reversed(active_conditions.items())
                    )
                active_conditions[last_condition] = not last_value

                if not self.resolve_conditions:
                    node_key, node_value = self._select_node_type(
                        "condition", last_condition, None
                    )
                    top.add(node_key, node_value)

                    node_key, node_value = self._select_node_type(
                        "condition", last_condition, not last_value
                    )
                    top.add(node_key, node_value)
                    continue

            if line.startswith('#endif'):
                last_condition, _ = active_conditions.popitem(last=True)
                if not self.resolve_conditions:
                    node_key, node_value = self._select_node_type(
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

            if line.startswith(comment_chars):
                char = line[0]
                comment = line[1:].strip()
                node_key, node_value = self._select_node_type(
                    "comment", char, comment
                )
                top.add(node_key, node_value)
                continue

            if line.startswith("#include"):
                include = line.strip("#include").lstrip()
                node_key, node_value = self._select_node_type(
                    "include", include
                )
                top.add(node_key, node_value)
                continue

            if line.startswith('['):
                _new_section = line.strip(' []').casefold()
                node_type = self.__node_value_types.get(_new_section, None)
                if node_type is None:
                    # Should not happen for compliant topologies
                    if self.verbose:
                        print(f"Unknown section {_new_section}")

                    node_key, node_value = self._select_node_type(
                        "section", _new_section
                    )
                    top.add(node_key, node_value)
                    active_section = node_value
                    continue

                if (node_type.category < active_category) and self.verbose:
                    print(f"Inconsistent section {_new_section}")
                else:
                    active_category = node_type.category

                issubsection = issubclass(
                    node_type, self.__node_value_types["subsection"]
                    )

                if issubsection:
                    node_value = node_type(
                        section=weakref.proxy(active_section)
                        )
                else:
                    node_value = node_type()
                    active_section = node_value

                node_key = node_value._make_node_key()
                top.add(node_key, node_value)
                continue

            if active_section._node_key_name == "defaults":
                if not self.ignore_comments:
                    line, comment = self.split_comment(line)
                else:
                    comment = None

                args = line.split()
                node_key, node_value = self._select_node_type(
                    "defaults_entry", *args, comment=comment
                )
                top.add(node_key, node_value)
                continue

            node_key, node_value = self._select_node_type(
                "generic", line
            )
            top.add(node_key, node_value)

        return top

    def _select_node_type(self, name, *args, **kwargs):
        node_type = self.__node_value_types[name]
        node_value = node_type(*args, **kwargs)
        node_key = node_value._make_node_key()
        return node_key, node_value

    def split_comment(self, line):
        split = False
        split_at = len(line)
        for char in self.comment_chars:
            if char not in line:
                continue

            split_at = min(split_at, line.index(char))

        if split:
            line = line[:split_at]
            comment = line[split_at:]
        else:
            comment = None

        return line, comment

class Node:
    __slots__ = ["prev", "next", "key", "value", '__weakref__']

    def __repr__(self):
        k = self.key if hasattr(self, "key") else None
        v = self.value if hasattr(self, "value") else None
        attr_str = f"(key={k!r}, value={v!r})"
        return f"{type(self).__name__}{attr_str}"


class AlwayGreater:
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

    call = 'gmx -h'
    feedback = subprocess.run(
        shlex.split(call),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding='utf8'
        )

    if feedback.returncode != 0:
        return None, None

    _feedback = feedback.stderr.split('\n')

    gmx_exe = None
    gmx_shared = None

    for line in _feedback:
        if line.startswith('Executable'):
            gmx_exe = pathlib.Path(line.split()[-1])
        if line.startswith('Data prefix'):
            gmx_shared = pathlib.Path(line.split()[-1]) / 'share/gromacs/top'

    return gmx_exe, gmx_shared


def ensure_proxy(obj):
    """Return a proxy of an object avoiding proxy of proxy"""

    if not isinstance(obj, (weakref.ProxyType, weakref.CallableProxyType)):
        return weakref.proxy(obj)

    return obj
