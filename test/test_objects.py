import pytest

import mdparser.topology as mdtop


class TestGromacsTop:

    def test_representation(self):

        top = mdtop.GromacsTop()
        assert f"{top!r}" == "GromacsTop()"
        assert f"{top!s}" == ""

    def test_node_operations(self):
        node_list = [
            ("node1", "foo"), ("node2", "bar"), ("node3", "baz"),
            ("node4", "brawl")
        ]

        top = mdtop.GromacsTop()
        assert len(top) == 0

        for count, (k, v) in enumerate(node_list, 1):
            top.add(k, mdtop.GenericNodeValue(v))
            assert top[k].value.value == v
            assert len(top) == count

        for i in range(4):
            assert top[i].value.value == node_list[i][1]

        node_value_slice = [x.value.value for x in top[1:3]]
        assert node_value_slice == [x[1] for x in node_list[1:3]]

        assert ("node2" in top) is True

        with pytest.raises(KeyError):
            top.add("node2", mdtop.GenericNodeValue("garbage"))

        top.discard("node2")
        assert len(top) == 3
        assert ("node2" in top) is False

        top.discard("garbage")

        for node, expected_key in zip(top, ["node1", "node3", "node4"]):
            assert node.key == expected_key

        for node, expected_key in zip(
                reversed(top),
                ["node4", "node3", "node1"]):
            assert node.key == expected_key

        top.replace("node3", mdtop.GenericNodeValue("balthazar"))
        assert top[1].value.value == "balthazar"

        top.insert(1, "new", mdtop.GenericNodeValue("cato"))
        top.insert(10, "other", mdtop.GenericNodeValue("brick"))

        with pytest.raises(IndexError):
            _ = top[10]

        with pytest.raises(ValueError):
            _ = top[[1, 2]]

        assert top[1].value.value == "cato"
        assert top[-1].value.value == "brick"

        assert top.index("new") == 1
        assert top.index("other", 2, 5) == 4

        with pytest.raises(ValueError):
            _ = top.index("other", 2, 4)

        with pytest.raises(ValueError):
            _ = top.index("garbage")

    def test_info(self):

        top = mdtop.GromacsTop()

        assert top.includes_resolved is True
        assert top.conditions_resolved is True

        top.add("Include", mdtop.Include("amber/ffx.itp"))
        top.add("check_POSRES", mdtop.Condition("POSRES", True))
        top.add("end_POSRES", mdtop.Condition("POSRES", None))

        assert top.includes_resolved is False
        assert top.conditions_resolved is False

    def test_find_complement(self):
        top = mdtop.GromacsTop()
        top.add("if", mdtop.Condition("some", True))
        top.add("entry", mdtop.GenericNodeValue("important"))
        top.add("end", mdtop.Condition("some", None))

        node = top[-1]
        complement = top.find_complement(node)

        assert isinstance(complement, mdtop.Node)


class TestNode:

    def test_representation(self):
        node = mdtop.Node()

        assert f"{node!r}" == "Node(key=None, value=None)"

        node.key = "key"
        node.value = "value"

        assert f"{node!r}" == "Node(key='key', value='value')"
