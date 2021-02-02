import mdparser.topology as mdtop
from . import _gmx_nodes


def get_subsections(top, section_node):
    subsections = []
    start = section_node
    while True:
        next_section = top.get_next_node_of_type(
            start,
            node_type=mdtop.DEFAULT_NODE_VALUE_TYPES["section"])

        if not isinstance(
                next_section.value,
                mdtop.DEFAULT_NODE_VALUE_TYPES["subsection"]):
            break

        subsections.append(next_section)
        start = next_section

    return subsections


def get_last_entry(top, section_node):
    current = section_node
    while isinstance(
            current.next.value,
            mdtop.DEFAULT_NODE_VALUE_TYPES["entry"]):
        current = current.next

    return current
