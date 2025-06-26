import pytest

from mdparser.topology import GromacsTopology, GromacsTopologyParser


class TestParseTopologies:
    """Regression tests for parsing of example topology files"""

    @pytest.mark.parametrize(
        "filename,parserkwargs",
        [
            ("empty.top", {}),
            ("comment.top", {}),
            ("comment_multiline.top", {}),
            ("comment.top", {"ignore_comments": False}),
            ("comment_multiline.top", {"ignore_comments": False}),
            ("ion.top", {}),
            ("ion.top", {"ignore_comments": False}),
            pytest.param(
                "ion.top",
                {"include_shared": True, "ignore_comments": False},
                marks=pytest.mark.needs_gmx,
            ),
            pytest.param(
                "ion.top",
                {"include_shared": True, "resolve_conditions": False},
                marks=pytest.mark.needs_gmx,
            ),
            pytest.param(
                "ion.top",
                {"include_shared": True, "include_blacklist": ["forcefield.itp"]},
                marks=pytest.mark.needs_gmx,
            ),
            ("two_ions.top", {"definitions": {"POSRES": True}}),
            ("two_ions.top", {"include_local": False, "definitions": {"POSRES": True}}),
            ("two_ions.top", {"use_relative_local_paths": False, "definitions": {"POSRES": True}}),
            ("two_ions.top", {"use_relative_local_paths": False, "local_paths": ["test_parse_topologies"], "definitions": {"POSRES": True}}),
            ("two_ions.top", {"include_shared": True, "use_default_shared_paths": False, "resolve_conditions": False}),
        ],
    )
    def test_parse(self, datadir, file_regression, filename, parserkwargs):
        parser = GromacsTopologyParser(**parserkwargs)
        with open(datadir / filename) as topfile:
            topology = parser.read(topfile)

        assert isinstance(topology, GromacsTopology)

        regression_str = ""
        for node in topology:
            regression_str += f"{node.key:<20} {node.value!s}\n\n"

        file_regression.check(regression_str)
