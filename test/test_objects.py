import pathlib
import weakref

import pytest

import mdparser.topology as mdtop
from mdparser import _gmx_nodes


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
            top.add(k, _gmx_nodes.GenericNodeValue(v))
            assert top[k].value.value == v
            assert len(top) == count

        for i in range(4):
            assert top[i].value.value == node_list[i][1]

        node_value_slice = [x.value.value for x in top[1:3]]
        assert node_value_slice == [x[1] for x in node_list[1:3]]

        assert ("node2" in top) is True

        with pytest.raises(KeyError):
            top.add("node2", _gmx_nodes.GenericNodeValue("garbage"))

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

        top.replace("node3", _gmx_nodes.GenericNodeValue("balthazar"))
        assert top[1].value.value == "balthazar"

        top.insert(1, "new", _gmx_nodes.GenericNodeValue("cato"))
        top.insert(10, "other", _gmx_nodes.GenericNodeValue("brick"))

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

        top.relative_insert(
            top[2], "special", _gmx_nodes.GenericNodeValue("grubbs")
            )

        assert top[3].value.value == "grubbs"

        top.relative_insert(
            top[3], "slurb", _gmx_nodes.GenericNodeValue("balaz"),
            forward=False
            )

        assert top[3].value.value == "balaz"

    def test_block_insert(self):
        def set_up():
            top = mdtop.GromacsTop()
            top.add("1", _gmx_nodes.GenericNodeValue("1"))
            top.add("2", _gmx_nodes.GenericNodeValue("2"))
            top.add("3", _gmx_nodes.GenericNodeValue("3"))

            node = mdtop.Node()
            node.value = _gmx_nodes.GenericNodeValue("4")
            node.key = "4"

            other = mdtop.Node()
            other.value = _gmx_nodes.GenericNodeValue("5")
            other.key = "5"

            node.connect(other)

            return top, node, other

        top, node, other = set_up()
        top.block_insert(top[1], node, other)
        assert [x.value.value for x in top] == ["1", "2", "4", "5", "3"]

        top, node, other = set_up()
        top.block_insert(top[1], node, other, forward=False)
        assert [x.value.value for x in top] == ["1", "4", "5", "2", "3"]

    def test_info(self):

        top = mdtop.GromacsTop()

        assert top.includes_resolved is True
        assert top.conditions_resolved is True

        top.add("Include", _gmx_nodes.Include("amber/ffx.itp"))
        top.add("check_POSRES", _gmx_nodes.Condition("POSRES", True))
        top.add("end_POSRES", _gmx_nodes.Condition("POSRES", None))

        assert top.includes_resolved is False
        assert top.conditions_resolved is False

    def test_find_complement(self):
        top = mdtop.GromacsTop()
        top.add("if", _gmx_nodes.Condition("some", True))
        top.add("entry", _gmx_nodes.GenericNodeValue("important"))
        top.add("end", _gmx_nodes.Condition("some", None))

        node = top[-1]
        complement = top.find_complement(node)

        assert isinstance(complement, mdtop.Node)

    def test_get_next_node_with_nvtype(self):
        top = mdtop.GromacsTop()

        with pytest.raises(ValueError):
            top.get_next_node_with_nvtype()

        with pytest.raises(LookupError):
            top.get_next_node_with_nvtype(
                nvtype=_gmx_nodes.GenericNodeValue
                )

        top.add("section", _gmx_nodes.Section("sec"))
        top.add("entry1", _gmx_nodes.SectionEntry("sec_entry"))
        top.add("subsection", _gmx_nodes.Subsection("subsec"))
        top.add("entry2", _gmx_nodes.SectionEntry("subsec_entry"))
        top.add("another_section", _gmx_nodes.Section("another_sec"))

        node = top.get_next_node_with_nvtype(nvtype=_gmx_nodes.Section)
        assert node is top["section"]

        node = top.get_next_node_with_nvtype(
            start=top["section"],
            nvtype=_gmx_nodes.Section
            )
        assert node is top["subsection"]

        node = top.get_next_node_with_nvtype(
            start=top["section"],
            )
        assert node is top["subsection"]

        node = top.get_next_node_with_nvtype(
            start=top["section"],
            nvtype=_gmx_nodes.Section,
            exclude=_gmx_nodes.Subsection
            )
        assert node is top["another_section"]

        with pytest.raises(LookupError):
            node = top.get_next_node_with_nvtype(
                start=top["section"],
                stop=top["another_section"],
                nvtype=_gmx_nodes.Section,
                exclude=_gmx_nodes.Subsection
                )

        with pytest.raises(LookupError):
            node = top.get_next_node_with_nvtype(
                start=top["another_section"],
                stop=top["subsection"],
                nvtype=_gmx_nodes.Section,
                exclude=_gmx_nodes.Subsection,
                forward=False
                )

        node = top.get_next_node_with_nvtype(
            start=top["another_section"],
            nvtype=_gmx_nodes.Section,
            exclude=_gmx_nodes.Subsection,
            forward=False
            )
        assert node is top["section"]


class TestNode:

    def test_representation(self):
        node = mdtop.Node()

        assert f"{node!r}" == "Node(key=None, value=None)"

        node.key = "key"
        node.value = "value"

        assert f"{node!r}" == "Node(key='key', value='value')"

    def test_connect(self):
        node = mdtop.Node()
        other = mdtop.Node()

        node.connect(other)
        assert node.next is other

        node.connect(other, forward=False)
        assert other.next is node


class TestNodeValues:

    @pytest.mark.parametrize(
        "nvtype,init_values,expected_attrs",
        [
            (
                _gmx_nodes.GenericNodeValue,
                {"value": "value"},
                ["value"]
            ),
            (
                _gmx_nodes.Define,
                {"key": "key", "value": True},
                ["key", "value"]
            ),
        ]
    )
    def test_representations(self, nvtype, init_values, expected_attrs):
        node = nvtype(**init_values)

        expected_attr_str = ", ".join(
            f"{v!s}={init_values[v]!r}"
            for v in expected_attrs
            )
        assert f"{node!r}" == f"{type(node).__name__}({expected_attr_str})"

    def test_define_node(self):
        def_node = _gmx_nodes.Define("FF_AMBER", True)
        assert f"{def_node!s}" == "#define FF_AMBER"

        def_node = _gmx_nodes.Define("spc_torsion", "0 1 1 923.0")
        assert f"{def_node!s}" == "#define spc_torsion 0 1 1 923.0"

        def_node = _gmx_nodes.Define("FF_AMBER", False)
        assert f"{def_node!s}" == "#undef FF_AMBER"

    def test_defaults_entry_node(self):
        default_entry_node = _gmx_nodes.DefaultsEntry(
            "1", "2", "no", "1.0", "0.8333", "12", comment="abc"
        )

        assert f"{default_entry_node!s}" == " 1               2               no              1.0     0.8333  12      ; abc"

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "C            6      12.01    0.0000  A   3.39967e-01  3.59824e-01",
                " C         6   12.01    0.0    A 3.39967e-01 3.59824e-01 ; abc"
            ),
            (
                "opls_001   C	6      12.01100     0.500       A    3.75000e-01  4.39320e-01",
                " opls_001  C    6   12.011   0.5    A 3.75000e-01 4.39320e-01 ; abc"
            )
        ]
    )
    def test_atomtypes_entry(self, line, expected):

        atomtypes_entry_node = _gmx_nodes.AtomtypesEntry.from_line(
            *line.split(),
            comment="abc"
        )

        assert f"{atomtypes_entry_node!s}" == expected

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "  1    H    1     PROP    PH    1   0.398    1.008  CH3     0.0  15.035",
                " 1     H     1     PROP  PH    1     0.398  1.008  CH3   0.0    15.035 ; abc"
            )
        ]
    )
    def test_atoms_entry(self, line, expected):

        atomtypes_entry_node = _gmx_nodes.AtomsEntry.from_line(
            *line.split(),
            comment="abc"
        )

        assert f"{atomtypes_entry_node!s}" == expected

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "    6     7     1 1.000000e-01 3.138000e+05 1.000000e-01 3.138000e+05",
                "     6     7     1 1.000000e-01 3.138000e+05 1.000000e-01 3.138000e+05 ; abc"
            )
        ]
    )
    def test_bonds_entry(self, line, expected):

        bonds_entry_node = _gmx_nodes.BondsEntry.from_line(
            *line.split(),
            comment="abc"
        )

        assert f"{bonds_entry_node!s}" == expected

    def test_raw(self):
        strange_line = "This was will not be parsed correctly!"
        node = _gmx_nodes.SectionEntry.create_raw(
            strange_line
            )

        assert node._raw == strange_line

    def test_counting(self):
        nvtype = _gmx_nodes.GenericNodeValue
        nvtype.reset_count()
        assert nvtype._count == 0

        node1 = nvtype(1)
        assert node1.count == 1
        assert nvtype._count == 1

        node2 = nvtype(2)
        assert node1.count == 1
        assert node2.count == 2
        assert nvtype._count == 2

        nvtype.reset_count()
        assert node1.count == 1
        assert node2.count == 2
        assert nvtype._count == 0

        nvtype.reset_count(3)
        assert nvtype._count == 3

    def test_entries(self):

        section_entry_type = _gmx_nodes.SectionEntry

        section_entry = section_entry_type.from_line(
            "a b c".split(), comment="abc"
            )

        assert f"{section_entry!s}" == " ; abc"


class TestHelper:
    def test_always_greater(self):
        ag = mdtop.AlwaysGreater()
        assert ag > 1
        assert ag >= 10
        assert not (ag < 5)
        assert not (ag <= 50)
        assert not (ag == 0)

    def test_always_less(self):
        al = mdtop.AlwaysLess()
        assert al < 1
        assert al <= 10
        assert not (al > 5)
        assert not (al >= 50)
        assert not (al == 0)

    def test_ensure_proxy(self):
        node = mdtop.Node()
        proxy = weakref.proxy(node)

        assert isinstance(mdtop.ensure_proxy(proxy), weakref.ProxyType)
        assert isinstance(mdtop.ensure_proxy(node), weakref.ProxyType)

    @pytest.mark.parametrize(
        "include_path,include_blacklist,expected",
        [
            (
                pathlib.Path(
                    "/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"
                ),
                [pathlib.Path("forcefield.itp")],
                True
            ),
            (
                pathlib.Path(
                    "/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"
                ),
                [pathlib.Path("amber99sb-ildn")],
                True
            ),
            (
                "/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp",
                ["amber99sb-ildn"],
                True
            ),
            (
                pathlib.Path(
                    "/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"
                ),
                [pathlib.Path("dummy.dat"), pathlib.Path("amber99sb-ildn")],
                True
            ),
            (
                pathlib.Path(
                    "/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"
                ),
                [pathlib.Path("dummy.dat"), pathlib.Path("foo.bar")],
                False
            )
        ]
    )
    def test_path_in_blacklist(
            self, include_path, include_blacklist, expected):

        ignore = mdtop.path_in_blacklist(include_path, include_blacklist)

        assert ignore is expected
