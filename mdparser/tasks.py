from . import _gmx_nodes


def get_subsections(top, section_node):
    subsections = []
    start = section_node
    while True:
        next_section = top.get_next_node_of_type(
            start,
            node_type=_gmx_nodes.Section
            )

        if not isinstance(next_section.value, _gmx_nodes.Subsection):
            break

        subsections.append(next_section)
        start = next_section

    return subsections


def get_last_entry(top, section_node):
    current = section_node
    entry = None
    while isinstance(current.next.value, _gmx_nodes.SectionEntry):
        current = current.next
        entry = current.value

    return entry
