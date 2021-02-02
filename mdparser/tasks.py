from copy import deepcopy

import mdparser.topology as mdtop
from . import _gmx_nodes


def get_subsections(top, section_node):
    section_nvtype = mdtop.GromacsTop.select_nvtype("section")
    subsection_nvtype = mdtop.GromacsTop.select_nvtype("subsection")

    subsections = []
    start = section_node
    while True:
        next_section = top.get_next_node_with_nvtype(
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

    section_nvtype = mdtop.GromacsTop.select_nvtype("section")
    moleculetype_section_nvtype = mdtop.GromacsTop.select_nvtype(
        "moleculetype"
        )
    atoms_entry_nvtype = mdtop.GromacsTop.select_nvtype("atoms_entry")
    bonds_entry_nvtype = mdtop.GromacsTop.select_nvtype("bonds_entry")
    molecules_nvtype = mdtop.GromacsTop.select_nvtype("molecules")
    molecules_entry_nvtype = mdtop.GromacsTop.select_nvtype("molecules_entry")

    moleculetype_section_list = []

    moleculetype_section = top._root
    while True:
        try:
            moleculetype_section = top.get_next_node_with_nvtype(
                start=moleculetype_section,
                nvtype=moleculetype_section_nvtype
                )
        except LookupError:
            break
        else:
            moleculetype_section_list.append(moleculetype_section)

    if len(moleculetype_section_list) == 0:
        raise LookupError(
            "no moleculetypes found"
        )

    molecules_section = top.get_next_node_with_nvtype(
        nvtype=molecules_nvtype,
        forward=False
        )

    moleculetype_subsection_mapping = {}
    for moleculetype_section in moleculetype_section_list:
        moleculetype_entry = moleculetype_section.next
        key = moleculetype_entry.value.molecule
        subsection_list = get_subsections(top, moleculetype_section)
        moleculetype_subsection_mapping[key] = subsection_list

    atom_nr_offset = 0

    if name is None:
        name = moleculetype_section_list[0].next.value.molecule

    moleculetype_section_nvtype.reset_count(
        len(moleculetype_section_list)
        )

    hardroot = new_current = mdtop.Node()
    new_current.key, new_current.value = mdtop.GromacsTop.make_nvtype(
        "moleculetype"
        )

    new_next = mdtop.Node()
    new_next.key, new_next.value = mdtop.GromacsTop.make_nvtype(
        "moleculetype_entry", molecule=name, nrexcl=3
        )

    new_current.connect(new_next)
    new_current = new_next

    molecules_entry = molecules_section.next
    if not isinstance(molecules_entry.value, molecules_entry_nvtype):
        raise LookupError("no molecules entry found")

    while True:
        if not isinstance(molecules_entry.value, molecules_entry_nvtype):
            break

        molecule_name = molecules_entry.value.molecule
        molecule_count = molecules_entry.value.number

        subsection_list = moleculetype_subsection_mapping[molecule_name]

        for _ in range(molecule_count):
            for subsection in subsection_list:
                new_next = mdtop.Node()
                new_next.value = type(subsection.value)()
                new_next.key = new_next.value._make_node_key()
                new_current.connect(new_next)
                new_current = new_next

                subsection_entry = subsection.next
                while not isinstance(subsection_entry.value, section_nvtype):
                    new_next = deepcopy()
                    if isinstance(subsection_entry.value, atoms_entry_nvtype):
                        pass

                    subsection_entry = subsection_entry.next

        molecules_entry = molecules_entry.next

    return hardroot
