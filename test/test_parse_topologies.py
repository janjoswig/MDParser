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
            ("ion.top", {"include_shared": True}),
            ("ion.top", {"include_shared": True, "resolve_conditions": False})
            ]
        )
    def test_parse(
            self,
            datadir,
            file_regression,
            filename,
            parserkwargs
            ):
        parser = mdtop.GromacsTopParser(**parserkwargs)
        with open(datadir / filename) as topfile:
            topology = parser.read(topfile)

        assert isinstance(topology, mdtop.GromacsTop)

        file_regression.check(str(topology))
