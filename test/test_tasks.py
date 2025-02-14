import pytest

from mdparser import _base, _gmx_nodes, tasks
from mdparser.topology import GromacsTopologyParser, GromacsTopology


class TestTopologyTasks:
    
    def test_find_root_node(self):

        root = _base.Node(value=_base.RootNodeValue())
        node = _base.Node(value=_base.GenericNodeValue("node1"))
        node2 = _base.Node(value=_base.GenericNodeValue("node2"))
        node.connect(node2)

        with pytest.raises(RuntimeError):
            tasks.find_root(node)
            
        node2.connect(root)
        assert tasks.find_root(node) is root

        with pytest.raises(RuntimeError):
            tasks.find_root(node, max_n=1)
        
        with pytest.raises(RuntimeError):
            tasks.find_root(node, forward=False)
            
        root.connect(node)
        assert tasks.find_root(node, forward=False).prev.next is root
        
        node2.connect(node)
        
        with pytest.raises(RuntimeError):
            tasks.find_root(node)
    
    def test_get_next_node_with_nvtype(self):

        with pytest.raises(ValueError):
            tasks.get_next_node_with_nvtype()

        top = GromacsTopology()
        top.add("section", _gmx_nodes.Section("sec"))
        top.add("entry1", _gmx_nodes.SectionEntry("sec_entry"))
        top.add("subsection", _gmx_nodes.Subsection("subsec"))
        top.add("entry2", _gmx_nodes.SectionEntry("subsec_entry"))
        top.add("another_section", _gmx_nodes.Section("another_sec"))

        with pytest.raises(LookupError):
            tasks.get_next_node_with_nvtype(nvtype=_base.GenericNodeValue, top=top)

        node = tasks.get_next_node_with_nvtype(nvtype=_gmx_nodes.Section, top=top)
        assert node is top["section"]

        node = tasks.get_next_node_with_nvtype(
            start=top["section"], nvtype=_gmx_nodes.Section, top=top
        )
        assert node is top["subsection"]

        node = tasks.get_next_node_with_nvtype(
            start=top["section"], top=top
        )
        assert node is top["subsection"]

        node = tasks.get_next_node_with_nvtype(
            start=top["section"],
            nvtype=_gmx_nodes.Section,
            exclude=_gmx_nodes.Subsection,
            top=top
        )
        assert node is top["another_section"]

        with pytest.raises(LookupError):
            node = tasks.get_next_node_with_nvtype(
                start=top["section"],
                stop=top["another_section"],
                nvtype=_gmx_nodes.Section,
                exclude=_gmx_nodes.Subsection,
            )

        with pytest.raises(LookupError):
            node = tasks.get_next_node_with_nvtype(
                start=top["another_section"],
                stop=top["subsection"],
                nvtype=_gmx_nodes.Section,
                exclude=_gmx_nodes.Subsection,
                forward=False,
            )

        node = tasks.get_next_node_with_nvtype(
            start=top["another_section"],
            nvtype=_gmx_nodes.Section,
            exclude=_gmx_nodes.Subsection,
            forward=False,
    top=top
        )
        assert node is top["section"]

    
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
