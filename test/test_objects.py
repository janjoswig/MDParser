import pathlib
import weakref

import pytest

from mdparser import topology
from mdparser import _base, _gmx_nodes


class TestNode:
    def test_representation(self):
        node = topology.Node()

        assert f"{node!r}" == "Node(key=None, value=None)"

        node.key = "key"
        node.value = "value"

        assert f"{node!r}" == "Node(key='key', value='value')"

    def test_connect(self):
        node = topology.Node()
        other = topology.Node()

        node.connect(other)
        assert node.next is other
        assert isinstance(other.prev, weakref.ProxyType)
        assert node.is_forward_connected
        assert not node.is_backward_connected
        assert other.is_backward_connected
        assert not other.is_forward_connected

        node.connect(other, forward=False)
        assert other.next is node
        assert isinstance(node.prev, weakref.ProxyType)
        assert node.is_connected
        assert other.is_connected


class TestNodeValues:
    @pytest.mark.parametrize(
        "nvtype,init_values,expected_attrs",
        [
            (_base.GenericNodeValue, {"value": "value"}, ["value"]),
            (_gmx_nodes.Define, {"key": "key", "value": True}, ["key", "value"]),
        ],
    )
    def test_representations(self, nvtype, init_values, expected_attrs):
        node = nvtype(**init_values)

        expected_attr_str = ", ".join(
            f"{v!s}={init_values[v]!r}" for v in expected_attrs
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

        assert (
            f"{default_entry_node!s}"
            == "1               2               no              1.0     0.8333  12      ; abc"
        )

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "C            6      12.01    0.0000  A   3.39967e-01  3.59824e-01",
                "C         6   12.01    0.0    A 3.39967e-01 3.59824e-01 ; abc",
            ),
            (
                "opls_001   C	6      12.01100     0.500       A    3.75000e-01  4.39320e-01",
                "opls_001  C    6   12.011   0.5    A 3.75000e-01 4.39320e-01 ; abc",
            ),
        ],
    )
    def test_atomtypes_entry(self, line, expected):
        atomtypes_entry_node = _gmx_nodes.AtomtypesEntry.from_line(
            *line.split(), comment="abc"
        )

        assert f"{atomtypes_entry_node!s}" == expected

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "  1    H    1     PROP    PH    1   0.398    1.008  CH3     0.0  15.035",
                "1     H     1     PROP  PH    1      0.3980   1.008 CH3    0.0000  15.035 ; abc",
            )
        ],
    )
    def test_atoms_entry(self, line, expected):
        atomtypes_entry_node = _gmx_nodes.AtomsEntry.from_line(
            *line.split(), comment="abc"
        )

        assert f"{atomtypes_entry_node!s}" == expected

    @pytest.mark.parametrize(
        "line,expected",
        [
            (
                "    6     7     1 1.000000e-01 3.138000e+05 1.000000e-01 3.138000e+05",
                "6     7     1     1.000000e-01 3.138000e+05 1.000000e-01 3.138000e+05 ; abc",
            )
        ],
    )
    def test_bonds_entry(self, line, expected):
        bonds_entry_node = _gmx_nodes.BondsEntry.from_line(*line.split(), comment="abc")

        assert f"{bonds_entry_node!s}" == expected

    def test_raw(self):
        strange_line = "This was will not be parsed correctly!"
        node = _gmx_nodes.SectionEntry.create_raw(strange_line)

        assert node._raw == strange_line

    def test_counting(self):
        nvtype = _base.GenericNodeValue
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

        section_entry = section_entry_type.from_line("a b c".split(), comment="abc")

        assert f"{section_entry!s}" == "a b c ; abc"


class TestHelper:
    def test_always_greater(self):
        ag = topology.AlwaysGreater()
        assert ag > 1
        assert ag >= 10
        assert not (ag < 5)
        assert not (ag <= 50)
        assert not (ag == 0)

    def test_always_less(self):
        al = topology.AlwaysLess()
        assert al < 1
        assert al <= 10
        assert not (al > 5)
        assert not (al >= 50)
        assert not (al == 0)

    def test_ensure_proxy(self):
        node = topology.Node()
        proxy = weakref.proxy(node)

        assert isinstance(topology.ensure_proxy(proxy), weakref.ProxyType)
        assert isinstance(topology.ensure_proxy(node), weakref.ProxyType)

    @pytest.mark.parametrize(
        "include_path,include_blacklist,expected",
        [
            (
                pathlib.Path("/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"),
                [pathlib.Path("forcefield.itp")],
                True,
            ),
            (
                pathlib.Path("/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"),
                [pathlib.Path("amber99sb-ildn")],
                False,
            ),
            (
                pathlib.Path("/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"),
                [pathlib.Path("amber99sb-ildn/forcefield.itp")],
                True,
            ),
            (
                pathlib.Path("/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"),
                [pathlib.Path("dummy.dat"), pathlib.Path("forcefield.itp")],
                True,
            ),
            (
                pathlib.Path("/usr/share/gromacs/top/amber99sb-ildn/forcefield.itp"),
                [pathlib.Path("dummy.dat"), pathlib.Path("foo.bar")],
                False,
            ),
        ],
    )
    def test_path_in_blacklist(self, include_path, include_blacklist, expected):
        ignore = topology.path_in_paths(include_path, include_blacklist)
        assert ignore is expected
