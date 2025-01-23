import pytest

from mdparser import topology
from mdparser import _base, _gmx_nodes


class TestGromacsTopology:
    def test_representation_empty(self):
        top = topology.GromacsTopology()
        assert f"{top!r}" == "GromacsTopology()"
        assert f"{top!s}" == ""

    def test_representation(self):
        top = topology.GromacsTopology()
        top.add("node", _base.GenericNodeValue("node"))
        assert f"{top!r}" == "GromacsTopology()"
        assert f"{top!s}" == "node\n"

    def test_node_operations(self):
        node_list = [
            ("node1", "foo"),
            ("node2", "bar"),
            ("node3", "baz"),
            ("node4", "brawl"),
        ]

        top = topology.GromacsTopology()
        assert len(top) == 0

        for count, (k, v) in enumerate(node_list, 1):
            top.add(k, _base.GenericNodeValue(v))
            assert top[k].value.value == v
            assert len(top) == count

        for i in range(4):
            assert top[i].value.value == node_list[i][1]
        # ["foo", "bar", "baz", "brawl"]

        node_value_slice = [x.value.value for x in top[1:3]]
        assert node_value_slice == [x[1] for x in node_list[1:3]]

        assert ("node2" in top) is True

        with pytest.raises(KeyError):
            top.add("node2", _base.GenericNodeValue("garbage"))

        top.discard("node2")
        assert len(top) == 3
        assert ("node2" in top) is False
        # ["foo", "baz", "brawl"]

        top.discard("garbage")

        for node, expected_key in zip(top, ["node1", "node3", "node4"]):
            assert node.key == expected_key

        for node, expected_key in zip(reversed(top), ["node4", "node3", "node1"]):
            assert node.key == expected_key

        top.replace("node3", _base.GenericNodeValue("balthazar"))
        assert top[1].value.value == "balthazar"
        # ["foo", "balthazar", "brawl"]

        top.insert(1, "new", _base.GenericNodeValue("cato"))
        top.insert(10, "other", _base.GenericNodeValue("brick"))
        # ["foo", "cato", "balthazar", "brawl", "brick"]

        with pytest.raises(IndexError):
            _ = top[10]

        assert [x.value.value for x in top[[1, 2]]] == ["cato", "balthazar"]

        assert top[1].value.value == "cato"
        assert top[-1].value.value == "brick"

        assert top.index("new") == 1
        assert top.index("other", 2, 5) == 4

        with pytest.raises(ValueError):
            _ = top.index("other", 2, 4)

        with pytest.raises(ValueError):
            _ = top.index("garbage")

        top.relative_insert(top[2], "special", _base.GenericNodeValue("grubbs"))

        assert top[3].value.value == "grubbs"

        top.relative_insert(
            top[3], "slurb", _base.GenericNodeValue("balaz"), forward=False
        )

        assert top[3].value.value == "balaz"

    @staticmethod
    def set_up():
        top = topology.GromacsTopology()
        top.add("1", _base.GenericNodeValue("1"))
        top.add("2", _base.GenericNodeValue("2"))
        top.add("3", _base.GenericNodeValue("3"))

        node = topology.Node()
        node.value = _base.GenericNodeValue("4")
        node.key = "4"

        other = topology.Node()
        other.value = _base.GenericNodeValue("5")
        other.key = "5"

        node.connect(other)

        return top, node, other

    def test_block_insert(self):

        top, node, other = self.set_up()
        top.block_insert(1, node, other)
        assert [x.value.value for x in top] == ["1", "4", "5", "2", "3"]
        assert set(top._nodes.keys()) == {"1", "2", "3", "4", "5"}

    def test_relative_block_insert(self):
        top, node, other = self.set_up()
        anchor = top[2]
        top.relative_block_insert(anchor, node, other)
        assert [x.value.value for x in top] == ["1", "2", "3", "4", "5"]
        assert set(top._nodes.keys()) == {"1", "2", "3", "4", "5"}

    def test_relative_block_insert_backward(self):
        top, node, other = self.set_up()
        anchor = top[2]
        top.relative_block_insert(anchor, node, other, forward=False)
        assert [x.value.value for x in top] == ["1", "2", "4", "5", "3"]
        assert set(top._nodes.keys()) == {"1", "2", "3", "4", "5"}

    def test_block_discard(self):
        top, *_ = self.set_up()
        start = top[0]
        end = top[-1]
        top.block_discard(start, end)
        assert set(top._nodes.keys()) == set()

    def test_info(self):
        top = topology.GromacsTopology()

        assert top.includes_resolved is True
        assert top.conditions_resolved is True

        top.add("Include", _gmx_nodes.Include("amber/ffx.itp"))
        top.add("check_POSRES", _gmx_nodes.Condition("POSRES", True))
        top.add("end_POSRES", _gmx_nodes.Condition("POSRES", None))

        assert top.includes_resolved is False
        assert top.conditions_resolved is False

    def test_find_complement(self):
        top = topology.GromacsTopology()
        top.add("if", _gmx_nodes.Condition("some", True))
        top.add("entry", _base.GenericNodeValue("important"))
        top.add("end", _gmx_nodes.Condition("some", None))

        node = top[-1]
        complement = top.find_complement(node)

        assert isinstance(complement, topology.Node)

    def test_get_next_node_with_nvtype(self):
        top = topology.GromacsTopology()

        with pytest.raises(ValueError):
            top.get_next_node_with_nvtype()

        with pytest.raises(LookupError):
            top.get_next_node_with_nvtype(nvtype=_base.GenericNodeValue)

        top.add("section", _gmx_nodes.Section("sec"))
        top.add("entry1", _gmx_nodes.SectionEntry("sec_entry"))
        top.add("subsection", _gmx_nodes.Subsection("subsec"))
        top.add("entry2", _gmx_nodes.SectionEntry("subsec_entry"))
        top.add("another_section", _gmx_nodes.Section("another_sec"))

        node = top.get_next_node_with_nvtype(nvtype=_gmx_nodes.Section)
        assert node is top["section"]

        node = top.get_next_node_with_nvtype(
            start=top["section"], nvtype=_gmx_nodes.Section
        )
        assert node is top["subsection"]

        node = top.get_next_node_with_nvtype(
            start=top["section"],
        )
        assert node is top["subsection"]

        node = top.get_next_node_with_nvtype(
            start=top["section"],
            nvtype=_gmx_nodes.Section,
            exclude=_gmx_nodes.Subsection,
        )
        assert node is top["another_section"]

        with pytest.raises(LookupError):
            node = top.get_next_node_with_nvtype(
                start=top["section"],
                stop=top["another_section"],
                nvtype=_gmx_nodes.Section,
                exclude=_gmx_nodes.Subsection,
            )

        with pytest.raises(LookupError):
            node = top.get_next_node_with_nvtype(
                start=top["another_section"],
                stop=top["subsection"],
                nvtype=_gmx_nodes.Section,
                exclude=_gmx_nodes.Subsection,
                forward=False,
            )

        node = top.get_next_node_with_nvtype(
            start=top["another_section"],
            nvtype=_gmx_nodes.Section,
            exclude=_gmx_nodes.Subsection,
            forward=False,
        )
        assert node is top["section"]