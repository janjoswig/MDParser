import pytest

from mdparser import tasks
from mdparser.topology import GromacsTopologyParser


class TestTopologyTasks:
    def test_get_subsections(self, tasks_top):
        first_molecule = tasks.get_next_node_with_nvtype(
            nvtype="moleculetype", top=tasks_top
        )
        subsections = tasks.get_subsections(first_molecule, top=tasks_top)

        assert len(subsections) == 2
        assert isinstance(subsections[0].value, tasks_top.select_nvtype("atoms"))
        assert isinstance(subsections[1].value, tasks_top.select_nvtype("bonds"))

    def test_get_last_entry(self, tasks_top):
        first_atoms = tasks.get_next_node_with_nvtype(
            nvtype="atoms", top=tasks_top
        )
        last_entry = tasks.get_last_entry(first_atoms, top=tasks_top)

        assert last_entry is not None
        assert isinstance(last_entry.value, tasks_top.select_nvtype("atoms_entry"))
        assert last_entry.value.type == "B"

    def test_merge_molecules(self, tasks_top, file_regression):
        tasks.merge_molecules(tasks_top, name="new")

        regression_string = ""
        for node in tasks_top:
            regression_string += f"{node.value!s}\n\n"

        file_regression.check(regression_string)

    @pytest.mark.needs_gmx
    @pytest.mark.parametrize(
        "filename,name",
        [
            ("qmmm.top", "QMMM_model"),
            ("qmmm_water.top", "QMMM_model"),
            ("qmmm_tip4p.top", None),
        ],
    )
    def test_merge_qmmm_molecules(self, filename, name, datadir, file_regression):
        parser = GromacsTopologyParser(
            include_shared=True, include_blacklist=["forcefield.itp"]
        )
        with open(datadir / filename) as topfile:
            topology = parser.read(topfile)

        tasks.merge_molecules(topology, name=name)

        file_regression.check(str(topology))

    def test_fail_merge_when_no_molecule(self, datadir):
        parser = GromacsTopologyParser()
        with open(datadir / "no_molecule.top") as topfile:
            topology = parser.read(topfile)

        with pytest.raises(LookupError):
            tasks.merge_molecules(topology)
