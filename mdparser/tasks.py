from copy import copy
from typing import List, Optional, Tuple, Type, Union

from mdparser import topology
from mdparser._base import (
    Node,
    NodeValue,
    GenericNodeValue,
    RootNodeValue,
    ensure_proxy,
    unproxy_node,
    get_node_path,
)


def find_root(
    node: Node, max_n: int = 10000, forward: bool = True, strict: bool = True
) -> Node:
    """Look for the root node

    Note:
        Depends on the root node having a `RootNodeValue` value.

    Args:
        node: node to start from

    Keyword args:
        max_n: maximum number of subsequent nodes to check before aborting.
            Avoids problems with infinite chains.
        forward: If `True`, search forward.  If `False`, search backward.
        strict: If `True`, raise an error if the root node is not found. If `False`,
            returns the last checked node.

    Returns:
        If successful, returns the root node. Otherwise, returns the last checked node,
        unless `strict=True`.
    """

    if forward is True:
        goto = "next"
    else:
        goto = "prev"

    current_node = node
    iteration = 0
    while not isinstance(current_node.value, RootNodeValue):
        current_node = getattr(current_node, goto)

        if current_node is node:
            if strict:
                raise RuntimeError(
                    "Circular node chain detected without finding root node"
                )
            return current_node

        if current_node is None:
            if strict:
                raise RuntimeError(
                    "End of node chain reached without finding root node"
                )
            return current_node

        iteration += 1
        if iteration >= max_n:
            if strict:
                raise RuntimeError(
                    f"Maximum number of nodes ({max_n}) reached without finding root node"
                )
            return current_node

    return current_node


def _prepare_node_search(
    start: Optional[Node] = None,
    stop: Optional[Node] = None,
    nvtype: Optional[Union[str, Type[NodeValue]]] = None,
    exclude: Optional[Tuple[Type[NodeValue]]] = None,
    forward: bool = True,
    top: Optional[topology.Topology] = None,
):
    if start is None:
        if nvtype is None:
            raise ValueError("If `start=None`, a node type must be specified")
        if top is None:
            raise ValueError("If `start=None`, a topology must be specified")
        start = top._root

    if stop is None:
        if top is None:
            raise ValueError("If `stop=None`, a topology must be specified")
        stop = top._root

    if nvtype is None:
        assert start is not None
        if start.value is None:
            raise ValueError("Start node has no node value to infer nvtype from")
        nvtype = type(start.value)

    if isinstance(nvtype, str):
        if top is None:
            raise ValueError(
                "If `nvtype` is of type `str`, a topology must be specified"
            )
        nvtype = top.select_nvtype(nvtype)

    if exclude is None:
        exclude = tuple()

    if forward is True:
        goto = "next"
    else:
        goto = "prev"

    return start, stop, nvtype, exclude, goto


def get_nodes_with_nvtype(
    start: Optional[Node] = None,
    stop: Optional[Node] = None,
    nvtype: Optional[Union[str, Type[NodeValue]]] = None,
    exclude: Optional[Tuple[Type[NodeValue]]] = None,
    forward: bool = True,
    top: Optional[topology.Topology] = None,
):
    """Search for nodes of specific type

    Args:
        start: :obj:`Node` to start from. If `None`, `nvtype`
            and `top`
            must be given and search starts at the beginning.
        stop: :obj:`Node` to stop at.  If `None`, `top`
            must be given to search until its end.
        nvtype: Type of node value to search for.
            If `None`, search for same type as start.
            If a string, `top` must be given.
        exclude: Exclude these node types from search.
        forward: If `True`, search topology forwards.  If `False`,
            search backwards.
        top: If not `None`, a topology instance to query in case,
            `start` or `stop` are `None` or `nvtype` is of type `str`.
    """

    start, stop, nvtype, exclude, goto = _prepare_node_search(
        start, stop, nvtype, exclude, forward, top
    )

    found_nodes = []
    node = unproxy_node(getattr(start, goto))
    while node is not stop:
        if isinstance(node.value, nvtype) and not isinstance(node.value, exclude):
            found_nodes.append(node)
        node = unproxy_node(getattr(node, goto))

    return found_nodes


def get_next_node_with_nvtype(
    start: Optional[Node] = None,
    stop: Optional[Node] = None,
    nvtype: Optional[Union[str, Type[NodeValue]]] = None,
    exclude: Optional[Tuple[Type[NodeValue]]] = None,
    forward: bool = True,
    top: Optional[topology.Topology] = None,
):
    """Search for another node

    Args:
        start: :obj:`Node` to start from. If `None`, `nvtype`
            and `top`
            must be given and search starts at the beginning.
        stop: :obj:`Node` to stop at.  If `None`, `top`
            must be given to search until its end.
        nvtype: Type of node value to search for.
            If `None`, search for same type as start.
            If a string, `top` must be given.
        exclude: Exclude these node types from search.
        forward: If `True`, search topology forwards.  If `False`,
            search backwards.
        top: If not `None`, a topology instance to query in case,
            `start` or `stop` are `None` or `nvtype` is of type `str`.
    """

    start, stop, nvtype, exclude, goto = _prepare_node_search(
        start, stop, nvtype, exclude, forward, top
    )

    node = unproxy_node(getattr(start, goto))
    while node is not stop:
        if isinstance(node.value, nvtype) and not isinstance(node.value, exclude):
            return unproxy_node(node)
        node = unproxy_node(getattr(node, goto))

    raise LookupError(f"Node of type {nvtype} not found")


def get_subsections(node: Node, top: topology.Topology):
    section_nvtype = top.select_nvtype("section")
    subsection_nvtype = top.select_nvtype("subsection")

    subsections = []
    start = node
    while True:
        try:
            next_section = get_next_node_with_nvtype(
                start, nvtype=section_nvtype, top=top
            )
        except LookupError:
            break

        if not isinstance(next_section.value, subsection_nvtype):
            break

        subsections.append(next_section)
        start = next_section

    return subsections


def get_entries(section_node: Node, top: topology.Topology) -> List[Node]:
    entry_nvtype = top.select_nvtype("section_entry")

    entries = []
    current = section_node
    while isinstance(current.next.value, entry_nvtype):
        current = current.next
        entries.append(current)

    return entries


def get_last_entry(section_node: Node, top: topology.Topology):
    entry_nvtype = top.select_nvtype("section_entry")

    current = section_node
    while isinstance(current.next.value, entry_nvtype):
        current = current.next

    return current


def merge_molecules(top: topology.Topology, name=None):
    section_nvtype = top.select_nvtype("section")
    moleculetype_section_nvtype = top.select_nvtype("moleculetype")
    atoms_entry_nvtype = top.select_nvtype("atoms_entry")
    p1term_entry_nvtype = top.select_nvtype("p1_term_entry")
    p2term_entry_nvtype = top.select_nvtype("p2_term_entry")
    p3term_entry_nvtype = top.select_nvtype("p3_term_entry")
    p4term_entry_nvtype = top.select_nvtype("p4_term_entry")
    virtual_sites1_entry_nvtype = top.select_nvtype("virtual_sites1_entry")
    exclusions_entry_nvtype = top.select_nvtype("exclusions_entry")
    molecules_nvtype = top.select_nvtype("molecules")
    molecules_entry_nvtype = top.select_nvtype("molecules_entry")

    moleculetype_section_list = []

    moleculetype_section = top._root
    while True:
        try:
            moleculetype_section = get_next_node_with_nvtype(
                start=moleculetype_section, nvtype=moleculetype_section_nvtype, top=top
            )
        except LookupError:
            break
        else:
            moleculetype_section_list.append(moleculetype_section)

    if len(moleculetype_section_list) == 0:
        raise LookupError("no moleculetypes found")

    molecules_section = get_next_node_with_nvtype(
        nvtype=molecules_nvtype, forward=False, top=top
    )

    moleculetype_subsection_mapping = {}
    for moleculetype_section in moleculetype_section_list:
        moleculetype_entry = moleculetype_section.next
        key = moleculetype_entry.value.molecule
        subsection_list = get_subsections(moleculetype_section, top=top)
        moleculetype_subsection_mapping[key] = subsection_list

    if name is None:
        name = moleculetype_section_list[0].next.value.molecule

    moleculetype_section_nvtype.reset_count(len(moleculetype_section_list))

    hardroot = new_current = topology.Node()
    new_current.key, new_current.value = topology.GromacsTopology.make_node_value(
        "moleculetype"
    )

    new_next = topology.Node()
    new_next.key, new_next.value = topology.GromacsTopology.make_node_value(
        "moleculetype_entry", molecule=name, nrexcl=3
    )

    new_current.connect(new_next)
    new_current = new_next

    atom_nr = 0

    molecules_entry = molecules_section
    while True:
        molecules_entry = molecules_entry.next

        if not isinstance(molecules_entry.value, molecules_entry_nvtype):
            break

        molecule_name = molecules_entry.value.molecule
        molecule_count = molecules_entry.value.number

        subsection_list = moleculetype_subsection_mapping[molecule_name]

        for _ in range(molecule_count):
            atom_nr_offset = atom_nr

            for subsection in subsection_list:
                new_next = topology.Node()
                new_next.value = type(subsection.value)()
                new_next.key = new_next.value._make_node_key()
                new_current.connect(new_next)
                new_current = new_next

                subsection_entry = subsection
                while True:
                    subsection_entry = subsection_entry.next

                    if isinstance(subsection_entry.value, section_nvtype):
                        break

                    new_next = topology.Node()
                    new_next.value = copy(subsection_entry.value)
                    new_next.key = new_next.value._make_node_key()
                    new_current.connect(new_next)
                    new_current = new_next

                    value = new_current.value
                    if isinstance(value, atoms_entry_nvtype):
                        value.nr += atom_nr_offset
                        atom_nr = value.nr
                        continue

                    if isinstance(value, p2term_entry_nvtype):
                        value.i += atom_nr_offset
                        value.j += atom_nr_offset
                        continue

                    if isinstance(value, p3term_entry_nvtype):
                        value.i += atom_nr_offset
                        value.j += atom_nr_offset
                        value.k += atom_nr_offset
                        continue

                    if isinstance(value, p4term_entry_nvtype):
                        value.i += atom_nr_offset
                        value.j += atom_nr_offset
                        value.k += atom_nr_offset
                        value.l += atom_nr_offset
                        continue

                    if isinstance(value, virtual_sites1_entry_nvtype):
                        for index in range(len(value.f)):
                            value.f[index] += atom_nr_offset
                        continue

                    if isinstance(value, p1term_entry_nvtype):
                        value.i += atom_nr_offset
                        continue

                    if isinstance(value, exclusions_entry_nvtype):
                        for index in range(len(value.indices)):
                            value.indices[index] += atom_nr_offset

    top.relative_block_insert(
        moleculetype_section_list[0], hardroot, new_current, forward=False
    )

    top.block_discard(
        moleculetype_section_list[0],
        get_last_entry(
            moleculetype_subsection_mapping[
                moleculetype_section_list[-1].next.value.molecule
            ][-1],
            top=top,
        ),
    )

    top.block_discard(
        molecules_section.next, get_last_entry(molecules_section, top=top)
    )

    key, value = topology.GromacsTopology.make_node_value(
        "molecules_entry", molecule=name, number=1
    )
    top.relative_insert(molecules_section, key, value)
