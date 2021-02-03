import pytest

import mdparser.topology as mdtop


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
            ("ion.top", {"include_shared": True, "ignore_comments": False}),
            ("ion.top", {"include_shared": True, "resolve_conditions": False}),
            ("ion.top", {
                "include_shared": True,
                "include_blacklist": ["forcefield.itp"]
                }),
            ("two_ions.top", {}),
            ]
        )
    def test_parse(
            self,
            datadir,
            file_regression,
            filename,
            parserkwargs):
        parser = mdtop.GromacsTopParser(**parserkwargs)
        with open(datadir / filename) as topfile:
            topology = parser.read(topfile)

        assert isinstance(topology, mdtop.GromacsTop)

        regression_str = ""
        for node in topology:
            regression_str += f"{node.key:<20} {node.value!s}\n\n"

        file_regression.check(regression_str)
