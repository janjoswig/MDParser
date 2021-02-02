import mdparser.topology as mdtop
from . import _gmx_nodes


def get_subsections(top, section_node):
    section_nvtype = mdtop.GromacsTop.select_nvtype("section")
    subsection_nvtype = mdtop.GromacsTop.select_nvtype("subsection")

    subsections = []
    start = section_node
    while True:
        next_section = top.get_next_node_of_type(
            start,
            nvtype=section_nvtype
            )

        if not isinstance(
                next_section.value,
                subsection_nvtype):
            break

        subsections.append(next_section)
        start = next_section

    return subsections


def get_last_entry(top, section_node):
    entry_nvtype = mdtop.GromacsTop.select_nvtype("entry")

    current = section_node
    while isinstance(
            current.next.value,
            entry_nvtype):
        current = current.next

    return current


def merge_molecules(top, name=None):

    raise NotImplementedError

    moleculetype_list = []
    moleculetype = top._root

    while True:
        try:
            moleculetype = top.get_next_node_of_type(
                start=moleculetype,
                nvtype=mdtop.DEFAULT_NODE_VALUE_TYPES["moleculetype"]
                )
        except LookupError:
            break
        else:
            moleculetype_list.append(moleculetype)

    if len(moleculetype_list) == 0:
        raise LookupError(
            "No molecules found"
        )

    molecules_section = top.get_next_node_of_type(
        start=top._root,
        nvtype=mdtop.DEFAULT_NODE_VALUE_TYPES["molecules"],
        forward=False
        )

    moleculetype_subsection_mapping = {}
    for moleculetype in moleculetype_list:
        key = moleculetype.next.value.name
        subsection_list = get_subsections(top, moleculetype)
        moleculetype_subsection_mapping[key] = subsection_list

    molecules_entry = molecules_section.next
    atom_nr_offset = 0

    if name is None:
        name = moleculetype_list[0].next.value.name

    mdtop.DEFAULT_NODE_VALUE_TYPES["moleculetype"].reset_count(
        len(moleculetype_list)
        )
    merged_moleculetype_value = mdtop.DEFAULT_NODE_VALUE_TYPES["moleculetype"]
    root = merged_moleculetype = mdtop.Node()
    merged_moleculetype.key = merged_moleculetype_value._make_node_key
    merged_moleculetype.value = merged_moleculetype_value

    merged_moleculetype_entry = mdtop.Node()
    merged_moleculetype_entry.value = mdtop.DEFAULT_NODE_VALUE_TYPES[
        "moleculetype"
        ](name=name, nrexcl=3)
    merged_moleculetype_entry.key = (
        merged_moleculetype_entry.value._make_node_key()
        )

    merged_moleculetype = merged_moleculetype.next

    while True:
        if not isinstance(
                molecules_entry,
                mdtop.DEFAULT_NODE_VALUE_TYPES["molecules_entry"]):
            break

        molecule_name = molecules_entry.value.molecule
        molecule_count = molecules_entry.value.number

        subsection_list = moleculetype_subsection_mapping[molecule_name]

        for _ in range(molecule_count):
            for subsection in subsection_list:
                new_subsection_value = type(subsection.value)()
                new_subsection = mdtop.Node()
                new_subsection.key = new_subsection_value._make_node_key()
                new_subsection.value = new_subsection_value
                merged_moleculetypes.connect(new_subsection)
