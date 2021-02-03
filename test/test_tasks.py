import pytest

import mdparser.topology as mdtop
import mdparser.tasks as mdtasks
from mdparser import _gmx_nodes


class TestTopologyTasks:

    def test_get_subsections(self, tasks_top):

        first_molecule = tasks_top.get_next_node_with_nvtype(
            nvtype=mdtop.DEFAULT_NODE_VALUE_TYPES["moleculetype"]
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

        first_atoms = tasks_top.get_next_node_with_nvtype(
            nvtype=tasks_top.select_nvtype("atoms")
            )
        last_entry = mdtasks.get_last_entry(first_atoms)

        assert isinstance(
            last_entry.value,
            mdtop.DEFAULT_NODE_VALUE_TYPES["atoms_entry"]
            )

        assert last_entry.value.type == "B"

    def test_merge_molecules(self, tasks_top, file_regression):
        mdtasks.merge_molecules(tasks_top, name="new")

        regression_string = ""
        for node in tasks_top:
            regression_string += f"{node.value!s}\n\n"

        file_regression.check(regression_string)

    def test_merge_qmmm_molecules(self, datadir, file_regression):

        parser = mdtop.GromacsTopParser(include_blacklist=["forcefield.itp"])
        with open(datadir / "qmmm.top") as topfile:
            topology = parser.read(topfile)

        mdtasks.merge_molecules(topology, name="QMMM_model")

        file_regression.check(str(topology))
