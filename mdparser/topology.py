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
        "entry": _gmx_nodes.SectionEntry,
        "defaults_entry": _gmx_nodes.DefaultsEntry,
        "atomtypes_entry": _gmx_nodes.AtomtypesEntry,
        "bondtypes_entry": _gmx_nodes.BondtypesEntry,    # raw
        "angletypes_entry": _gmx_nodes.AngletypesEntry,  # raw
        "pairtypes_entry": _gmx_nodes.PairtypesEntry,    # raw
        "dihedraltypes_entry": _gmx_nodes.DihedraltypesEntry,       # raw
        "constrainttypes_entry": _gmx_nodes.ConstrainttypesEntry,   # raw
        "nonbonded_params_entry": _gmx_nodes.NonbondedParamsEntry,  # raw
        "moleculetype_entry": _gmx_nodes.MoleculetypeEntry,
        "atoms_entry": _gmx_nodes.AtomsEntry,
        "bonds_entry": _gmx_nodes.BondsEntry,
        "pairs_entry": _gmx_nodes.PairsEntry,       # raw
        "pairs_nb_entry": _gmx_nodes.PairsNBEntry,  # raw
        "exclusions_entry": _gmx_nodes.ExclusionsEntry,
        "system_entry": _gmx_nodes.SystemEntry,
        "molecules_entry": _gmx_nodes.MoleculesEntry,
    }


class GromacsTop:

    __node_value_types = DEFAULT_NODE_VALUE_TYPES

    def __init__(self):
        self._nodes = dict()
        self._hardroot = Node()
        self._root = root = weakref.proxy(self._hardroot)
        root.prev = root.next = root

    def __str__(self):
        return_str = ""
        for node in self:
            if isinstance(node.value, self.__node_value_types["section"]):
                return_str += "\n"
            return_str += f"{node.value!s}\n"

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
        """Return number of linked nodes"""

        length = 0

        for length, _ in enumerate(self, 1):
            pass

        return length

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
            f"items can only be queried by 'str' (node key), "
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

    @classmethod
    def make_nvtype(cls, name, *args, **kwargs):
        """Retrieve node type by name, initialize, and make key"""

        nvtype = cls.__node_value_types[name]
        node_value = nvtype(*args, **kwargs)
        node_key = node_value._make_node_key()

        return node_key, node_value

    @classmethod
    def select_nvtype(cls, name):
        """Retrieve node type by name"""
        return cls.__node_value_types[name]

    def add(self, key, value) -> None:

        node = self._check_key_and_add_new_node(key)

        root = self._root
        last = root.prev
        node.prev, node.next, node.key, node.value = last, root, key, value
        last.next = node
        root.prev = weakref.proxy(node)

    def pop(self, key):
        node = self._nodes.pop(key)
        node.prev.next = node.next
        node.next.prev = node.prev
        return node

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
            stop = AlwaysGreater()

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

    def relative_insert(self, node, key, value, forward=True):
        """Insert node after/before other node"""

        new_node = self._check_key_and_add_new_node(key)

        if forward is True:
            new_node.prev, new_node.next = node.next.prev, node.next
            new_node.next.prev = weakref.proxy(new_node)
            node.next = new_node
        else:
            new_node.prev, new_node.next = node.prev, node
            new_node.prev.next = new_node
            node.prev = weakref.proxy(new_node)

        new_node.key, new_node.value = key, value

    def get_next_node_with_nvtype(
            self, start=None, stop=None, nvtype=None,
            exclude=None, forward=True):
        """Search topology for another node

        Args:
            start: obj:`Node` to start from.  If `None`, an `nvtype`
                must be given and search starts at the beginning.
            stop: :obj:`Node` to stop at.  If `None`, search until end.
            nvtype: Type of node value to search for.
                If `None`, search for same type as start.
            exclude: Exclude node types from search.
            forward: If `True`, search topology forwards.  If `False`,
                search backwards.
        """
        if start is None:
            if nvtype is None:
                raise ValueError(
                    "If start=None, a node type must be specified"
                    )
            start = self._root

        if stop is None:
            stop = self._root

        if nvtype is None:
            nvtype = type(start.value)

        if exclude is None:
            exclude = ()

        if forward is True:
            goto = "next"
        else:
            goto = "prev"

        node = getattr(start, goto)

        while unproxy_node(node) is not stop:
            if not isinstance(node.value, nvtype):
                node = getattr(node, goto)
                continue

            if isinstance(node.value, exclude):
                node = getattr(node, goto)
                continue

            return unproxy_node(node)

        raise LookupError(f"Node of type {nvtype} not found")

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


class GromacsTopParser:
    """Read and write GROMACS topology files"""

    __top_type = GromacsTop

    def __init__(
            self,
            ignore_comments: bool = True,
            preprocess: bool = True,
            include_local: bool = True,
            include_shared: bool = False,
            local_paths: Optional[Iterable[Any]] = None,
            shared_paths: Optional[Iterable[Any]] = None,
            include_blacklist: Optional[Iterable[Any]] = None,
            definitions: Optional[Mapping[str, Any]] = None,
            resolve_conditions: bool = True,
            verbose: bool = True):

        self.ignore_comments = ignore_comments
        self.preprocess = preprocess
        self.include_local = include_local

        if local_paths is not None:
            local_paths = [pathlib.Path(p) for p in local_paths]
        self.local_paths = local_paths

        self.include_shared = include_shared

        if shared_paths is not None:
            shared_paths = [pathlib.Path(p) for p in shared_paths]
        self.shared_paths = shared_paths

        if include_blacklist is not None:
            include_blacklist = [pathlib.Path(f) for f in include_blacklist]
        self.include_blacklist = include_blacklist

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
            shared_paths=None,
            include_blacklist=None):
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

        if include_blacklist is not None:
            include_blacklist = [pathlib.Path(f) for f in include_blacklist]

        for line in file:
            if not line.startswith('#include'):
                yield line
                continue

            include_file = line.split()[1].strip('"')

            found_locally = False
            if include_local:
                for include_dir in _local_paths:
                    include_path = include_dir / include_file

                    if path_in_blacklist(include_path, include_blacklist):
                        continue

                    if not include_path.is_file():
                        continue

                    with open(include_path) as open_file:
                        yield from self.preprocess_includes(
                            open_file,
                            include_local=include_local,
                            local_paths=local_paths,
                            include_shared=include_shared,
                            shared_paths=shared_paths,
                            include_blacklist=include_blacklist,
                        )
                    found_locally = True
                    break

            found_shared = False
            if not found_locally and include_shared:
                for include_dir in shared_paths:
                    include_path = include_dir / include_file

                    if path_in_blacklist(include_path, include_blacklist):
                        continue

                    if not include_path.is_file():
                        continue

                    with open(include_path) as open_file:
                        yield from self.preprocess_includes(
                            open_file,
                            include_local=include_local,
                            local_paths=local_paths,
                            include_shared=include_shared,
                            shared_paths=shared_paths,
                            include_blacklist=include_blacklist,
                        )
                    found_shared = True
                    break

            if not (found_locally or found_shared):
                yield line

    def read(self, file: Iterable) -> GromacsTop:
        top = self.__top_type()

        if self.preprocess:
            file = self.preprocess_includes(
                file,
                include_local=self.include_local,
                local_paths=self.local_paths,
                include_shared=self.include_shared,
                shared_paths=self.shared_paths,
                include_blacklist=self.include_blacklist,
                )

        active_section = None
        active_supersection = None
        active_category = 0

        active_conditions = OrderedDict()
        active_definitions = {}
        active_definitions.update(self.definitions)

        for node_value_type in top._GromacsTop__node_value_types.values():
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

            if self.ignore_comments:
                line, _ = split_comment(line)

            line = line.strip()

            if line in ['', '\n', '\n\r']:
                continue

            if line.startswith('#define'):
                line = line.lstrip("#define").lstrip().split(maxsplit=1)
                if len(line) == 1:
                    node_key, node_value = top.make_nvtype(
                        "define", line[0], True
                    )
                    top.add(node_key, node_value)
                    active_definitions[line[0]] = True
                else:
                    node_key, node_value = top.make_nvtype(
                        "define", line[0], line[1]
                    )
                    top.add(node_key, node_value)
                    active_definitions[line[0]] = line[1]
                continue

            if line.startswith('#undef'):
                line = line.lstrip("#undef").lstrip()
                node_key, node_value = top.make_nvtype(
                    "define", line, False
                )
                top.add(node_key, node_value)
                _ = active_definitions.pop(line)
                continue

            if line.startswith('#ifdef'):
                line = line.lstrip('#ifdef').lstrip()
                active_conditions[line] = True
                if not self.resolve_conditions:
                    node_key, node_value = top.make_nvtype(
                        "condition", line, True
                    )
                    top.add(node_key, node_value)
                continue

            if line.startswith('#ifndef'):
                line = line.lstrip('#ifndef').lstrip()
                active_conditions[line] = False
                if not self.resolve_conditions:
                    node_key, node_value = top.make_nvtype(
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
                    node_key, node_value = top.make_nvtype(
                        "condition", last_condition, None
                    )
                    top.add(node_key, node_value)

                    node_key, node_value = top.make_nvtype(
                        "condition", last_condition, not last_value
                    )
                    top.add(node_key, node_value)
                    continue

            if line.startswith('#endif'):
                last_condition, _ = active_conditions.popitem(last=True)
                if not self.resolve_conditions:
                    node_key, node_value = top.make_nvtype(
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
                node_key, node_value = top.make_nvtype(
                    "comment", comment
                )
                top.add(node_key, node_value)
                continue

            if line.startswith("#include"):
                include = line.strip("#include").lstrip()
                node_key, node_value = top.make_nvtype(
                    "include", include
                )
                top.add(node_key, node_value)
                continue

            if line.startswith('['):
                _new_section = line.strip(' []').casefold()
                nvtype = top._GromacsTop__node_value_types.get(
                    _new_section, None
                    )
                if nvtype is None:
                    # Should not happen for compliant topologies
                    if self.verbose:
                        print(f"Unknown section {_new_section}")

                    node_key, node_value = top.make_nvtype(
                        "section", _new_section
                    )
                    top.add(node_key, node_value)
                    active_section = active_supersection = node_value
                    continue

                if (nvtype.category < active_category) and self.verbose:
                    print(f"Inconsistent section {_new_section}")
                else:
                    active_category = nvtype.category

                issubsection = issubclass(
                    nvtype, top._GromacsTop__node_value_types["subsection"]
                    )

                if issubsection:
                    node_value = nvtype(
                        section=weakref.proxy(active_supersection)
                        )
                    active_section = node_value
                else:
                    node_value = nvtype()
                    active_section = active_supersection = node_value

                node_key = node_value._make_node_key()
                top.add(node_key, node_value)
                continue

            if active_section is None:
                node_key, node_value = top.make_nvtype(
                    "comment", line
                )
                node_value._char = None
                top.add(node_key, node_value)
                continue

            expected_entry = f"{active_section._node_key_name}_entry"
            nvtype = top._GromacsTop__node_value_types.get(
                expected_entry, False
                )
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
            node_key, node_value = top.make_nvtype(
                "generic", line
            )
            top.add(node_key, node_value)

        return top


class Node:
    __slots__ = ["prev", "next", "key", "value", '__weakref__']

    def __init__(self):
        self.prev = None
        self.next = None
        self.key = None
        self.value = None

    def __repr__(self):
        attr_str = f"(key={self.key!r}, value={self.value!r})"
        return f"{type(self).__name__}{attr_str}"

    def connect(self, other, forward=True):
        """Link another node in forward/backward direction"""

        if forward is True:
            self.next = other
            other.prev = weakref.proxy(self)
        else:
            self.prev = weakref.proxy(other)
            other.next = self


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


def unproxy_node(node):
    return node.prev.next


def split_comment(line):
    if ";" in line:
        return tuple(line.split(";", maxsplit=1))
    return line, None


def path_in_blacklist(include_path, include_blacklist):
    if include_blacklist is None:
        return False

    include_path = str(include_path)

    for ignored in include_blacklist:
        if str(ignored) in include_path:
            return True

    return False
