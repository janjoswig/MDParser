import pytest

import mdparser.topology as mdtop
import mdparser.tasks as mdtasks
from mdparser import _gmx_nodes


class TestTopologyTasks:

    def test_get_subsections(self, tasks_top):

        first_molecule = tasks_top.get_next_node_of_type(
            node_type=mdtop.DEFAULT_NODE_VALUE_TYPES["moleculetype"]
            )
        subsections = mdtasks.get_subsections(tasks_top, first_molecule)
        assert len(subsections) == 2

        assert isinstance(
            subsections[0].value,
            mdtop.DEFAULT_NODE_VALUE_TYPES["atoms"]
            )

        assert isinstance(
            subsections[1].value,
            mdtop.DEFAULT_NODE_VALUE_TYPES["bonds"]
            )

    def test_get_last_entry(self, tasks_top):

        first_atoms = tasks_top.get_next_node_of_type(
            node_type=mdtop.DEFAULT_NODE_VALUE_TYPES["atoms"]
            )
        last_entry = mdtasks.get_last_entry(tasks_top, first_atoms)

        assert isinstance(
            last_entry.value,
            mdtop.DEFAULT_NODE_VALUE_TYPES["atoms_entry"]
            )

        assert last_entry.value.type == "B"