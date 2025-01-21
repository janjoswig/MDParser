from typing import Iterable

from ._base import NodeValue, make_formatter, trim_locals


class Define(NodeValue):
    """#define or #undef directives"""

    _node_key_name = "define"

    def __init__(self, key, value):
        super().__init__()
        self.key = key
        self.value = value

    def __str__(self):
        if not isinstance(self.value, bool):
            return f"#define {self.key} {self.value}"

        if self.value is True:
            return f"#define {self.key}"

        if self.value is False:
            return f"#undef {self.key}"

    def __repr__(self):
        return f"{type(self).__name__}(key={self.key!r}, value={self.value!r})"


class Condition(NodeValue):
    """#ifdef, #ifndef, #endif directives"""

    _node_key_name = "condition"

    def __init__(self, key, value, complement=None):
        super().__init__()
        self.key = key
        self.value = value
        self.complement = complement

    def __str__(self):
        if self.value is True:
            return f"#ifdef {self.key}"

        if self.value is False:
            return f"#ifndef {self.key}"

        if self.value is None:
            return "#endif"


class Section(NodeValue):
    """A regular section heading"""

    _node_key_name = "section"

    def __init__(self, title: str):
        super().__init__()
        self.title = title

    def __str__(self):
        return f"[ {self.title} ]"


class SpecializedSection(Section):
    _node_key_name = "special_section"
    category = 0
    allowed_occurrence = 0

    def __init__(self):
        super().__init__(self._node_key_name)


class DefaultsSection(SpecializedSection):
    _node_key_name = "defaults"
    allowed_occurrence = 1


class AtomtypesSection(SpecializedSection):
    _node_key_name = "atomtypes"


class BondtypesSection(SpecializedSection):
    _node_key_name = "bondtypes"


class AngletypesSection(SpecializedSection):
    _node_key_name = "angletypes"


class PairtypesSection(SpecializedSection):
    _node_key_name = "pairtypes"


class DihedraltypesSection(SpecializedSection):
    _node_key_name = "dihedraltypes"


class ConstrainttypesSection(SpecializedSection):
    _node_key_name = "constrainttypes"


class NonbondedParamsSection(SpecializedSection):
    _node_key_name = "nonbonded_params"


class MoleculetypeSection(SpecializedSection):
    _node_key_name = "moleculetype"
    category = 1


class SystemSection(SpecializedSection):
    _node_key_name = "system"
    category = 2
    allowed_occurrence = 1


class MoleculesSection(SpecializedSection):
    _node_key_name = "molecules"
    category = 2
    allowed_occurrence = 1


class Subsection(Section):
    """A subsection heading"""

    _node_key_name = "subsection"

    def __init__(self, title: str, section=None):
        super().__init__(title)
        self.section = section


class SpecializedSubsection(Subsection):
    _node_key_name = "special_subsection"
    category = 1
    allowed_occurrence = 0

    def __init__(self, section=None):
        super().__init__(self._node_key_name, section=section)


class AtomsSubsection(SpecializedSubsection):
    _node_key_name = "atoms"


class BondsSubsection(SpecializedSubsection):
    _node_key_name = "bonds"


class PairsSubsection(SpecializedSubsection):
    _node_key_name = "pairs"


class PairsNBSubsection(SpecializedSubsection):
    _node_key_name = "pairs_nb"


class AnglesSubsection(SpecializedSubsection):
    _node_key_name = "angles"


class DihedralsSubsection(SpecializedSubsection):
    _node_key_name = "dihedrals"


class ExclusionsSubsection(SpecializedSubsection):
    _node_key_name = "exclusions"


class ConstraintsSubsection(SpecializedSubsection):
    _node_key_name = "constraints"


class SettlesSubsection(SpecializedSubsection):
    _node_key_name = "settles"


class VirtualSites2Subsection(SpecializedSubsection):
    _node_key_name = "virtual_sites2"


class VirtualSites3Subsection(SpecializedSubsection):
    _node_key_name = "virtual_sites3"


class VirtualSites4Subsection(SpecializedSubsection):
    _node_key_name = "virtual_sites4"


class VirtualSitesNSubsection(SpecializedSubsection):
    _node_key_name = "virtual_sitesn"


class PositionRestraintsSubsection(SpecializedSubsection):
    _node_key_name = "position_restraints"


class DistanceRestraintsSubsection(SpecializedSubsection):
    _node_key_name = "distance_restraints"


class DihedralRestraintsSubsection(SpecializedSubsection):
    _node_key_name = "dihedral_restraints"


class OrientationRestraintsSubsection(SpecializedSubsection):
    _node_key_name = "orientation_restraints"


class AngleRestraintsSubsection(SpecializedSubsection):
    _node_key_name = "angle_restraints"


class AngleRestraintsZSubsection(SpecializedSubsection):
    _node_key_name = "angle_restraints_z"


class Comment(NodeValue):
    """Standalone full-line comment"""

    _node_key_name = "comment"

    def __init__(self, comment: str):
        super().__init__()
        self.comment = comment
        self._char = ";"

    def __str__(self):
        if self._char is None:
            return f"{self.comment}"
        else:
            return f"{self._char} {self.comment.__str__()}"


class Include(NodeValue):
    """#include directive"""

    _node_key_name = "include"

    def __init__(self, include: str):
        super().__init__()
        self.include = include

    def __str__(self):
        return f"#include {self.include.__str__()}"

    def __repr__(self):
        return f"{type(self).__name__}({self.include})"


class SectionEntry(NodeValue):
    """A section entry"""

    _node_key_name = "section_entry"
    _args = []

    def __init__(self, comment=None, **kwargs):
        super().__init__()

        for name, target_type, *_ in self._args:
            value = kwargs.get(name)
            if value is None:
                setattr(self, name, value)
                continue

            if target_type is None:
                continue

            try:
                value = target_type(value)
            except ValueError:
                if not isinstance(value, str):
                    raise TypeError(
                        f"Argument {name!r} should be 'str' or "
                        f"convertible to {target_type.__name__!r}"
                    )

            setattr(self, name, value)

        self.comment = comment
        self._raw = None

    def __copy__(self):
        kwargs = {arg_name: getattr(self, arg_name) for arg_name, *_ in self._args}
        copied = type(self)(**kwargs, comment=self.comment)
        copied._raw = self._raw

        return copied

    @classmethod
    def create_raw(cls, line):
        node_value = cls()
        node_value._raw = line
        return node_value

    @classmethod
    def from_line(cls, *args, comment=None):
        kwargs = {kw[0]: v for kw, v in zip(cls._args, args)}

        entry = cls(comment=comment, **kwargs)

        return entry

    def __str__(self):
        if self._raw is not None:
            return self._raw

        return_str = ""
        for name, *_, formatter in self._args:
            value = getattr(self, name)
            if value is None:
                continue

            if not isinstance(value, str) and isinstance(value, Iterable):
                for v in value:
                    return_str += f" {formatter(v)}"
                continue

            return_str += f" {formatter(value)}"

        return_str = self._finish_str(return_str)

        return return_str

    def __repr__(self):
        arg_name_repr = ", ".join(
            f"{arg_name!s}={getattr(self, arg_name)!r}" for arg_name, *_ in self._args
        )

        return f"{type(self).__name__}({arg_name_repr})"

    def _finish_str(self, string):
        if self.comment is not None:
            string += f" ; {self.comment}"

        string = string.rstrip()

        return string


class PropertyInvoker:
    """Invokes descriptor protocol for instance attributes"""

    def __setattr__(self, attr, value):
        try:
            got = super().__getattribute__(attr)
            got.__set__(self, value)
        except AttributeError:
            super().__setattr__(attr, value)

    def __getattribute__(self, attr):
        got = super().__getattribute__(attr)
        try:
            return got.__get__(self, type(self))
        except AttributeError:
            return got


class P1TermEntry(SectionEntry, PropertyInvoker):
    _node_key_name = "p1_term_entry"
    _args = [
        ("i", int, make_formatter(">5")),
        ("funct", int, make_formatter(">5")),
        ("c", None, make_formatter("1.6e")),
    ]

    def getc(self, index):
        def getter(self):
            return self.c[index]

        return getter

    def setc(self, index):
        def setter(self, value):
            self.c[index] = value

        return setter

    def delc(self, index):
        def deleter(self):
            del self.c[index]

        return deleter

    def __init__(self, i=None, funct=None, c=None, comment=None, **kwargs):
        locals_ = trim_locals(locals())

        super().__init__(**locals_, **kwargs)

        if c is None:
            c = []
        self.c = [float(x) for x in c]

        for index in range(len(self.c)):
            # Add instance specific properties "c0", "c1", ...
            setattr(
                self,
                f"c{index}",
                property(
                    fget=self.getc(index),
                    fset=self.setc(index),
                    fdel=self.delc(index),
                    doc="Access term coefficients",
                ),
            )

    @classmethod
    def from_line(cls, *args, comment=None):
        i, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None

        entry = cls(
            i=i,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class P2TermEntry(P1TermEntry):
    _node_key_name = "p2_term_entry"
    _args = [
        ("i", int, make_formatter(">5")),
        ("j", int, make_formatter(">5")),
        ("funct", int, make_formatter(">5")),
        ("c", None, make_formatter("1.6e")),
    ]

    def __init__(self, i=None, j=None, funct=None, c=None, comment=None):
        super().__init__(i=i, j=j, funct=funct, c=c, comment=comment)

    @classmethod
    def from_line(cls, *args, comment=None):
        i, j, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None

        entry = cls(
            i=i,
            j=j,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class P3TermEntry(P1TermEntry):
    _node_key_name = "p3_term_entry"
    _args = [
        ("i", int, make_formatter(">5")),
        ("j", int, make_formatter(">5")),
        ("k", int, make_formatter(">5")),
        ("funct", int, make_formatter(">5")),
        ("c", None, make_formatter("1.6e")),
    ]

    def __init__(self, i=None, j=None, k=None, funct=None, c=None, comment=None):
        super().__init__(i=i, j=j, k=k, funct=funct, c=c, comment=comment)

    @classmethod
    def from_line(cls, *args, comment=None):
        i, j, k, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None

        entry = cls(
            i=i,
            j=j,
            k=k,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class P4TermEntry(P1TermEntry):
    _node_key_name = "p4_term_entry"
    _args = [
        ("i", int, make_formatter(">5")),
        ("j", int, make_formatter(">5")),
        ("k", int, make_formatter(">5")),
        ("l", int, make_formatter(">5")),
        ("funct", int, make_formatter(">5")),
        ("c", None, make_formatter("1.6e")),
    ]

    def __init__(
        self, i=None, j=None, k=None, l=None, funct=None, c=None, comment=None
    ):
        super().__init__(i=i, j=j, k=k, l=l, funct=funct, c=c, comment=comment)

    @classmethod
    def from_line(cls, *args, comment=None):
        i, j, k, l, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None

        entry = cls(
            i=i,
            j=j,
            k=k,
            l=l,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class DefaultsEntry(SectionEntry):
    """Entry in defaults section"""

    _node_key_name = "defaults_entry"
    _args = [
        ("nbfunc", int, make_formatter("<15")),
        ("comb_rule", int, make_formatter("<15")),
        ("gen_pairs", str, make_formatter("<15")),
        ("fudgeLJ", float, make_formatter("<7")),
        ("fudgeQQ", float, make_formatter("<7")),
        ("n", int, make_formatter("<7")),
    ]

    def __init__(
        self,
        nbfunc=None,
        comb_rule=None,
        gen_pairs="no",
        fudgeLJ=None,
        fudgeQQ=None,
        n=None,
        comment=None,
    ):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)


class AtomtypesEntry(SectionEntry):
    _node_key_name = "atomtypes_entry"
    _args = [
        ("name", str, make_formatter("<9")),
        ("bond_type", str, make_formatter("<4")),
        ("at_num", int, make_formatter("<3")),
        ("mass", float, make_formatter("<8")),
        ("charge", float, make_formatter("<6")),
        ("ptype", str, make_formatter("<1")),
        ("sigma", float, make_formatter("1.5e")),
        ("epsilon", float, make_formatter("1.5e")),
    ]

    def __init__(
        self,
        name=None,
        bond_type=None,
        at_num=None,
        mass=None,
        charge=None,
        ptype=None,
        sigma=None,
        epsilon=None,
        comment=None,
    ):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)

    @classmethod
    def from_line(cls, *args, comment):
        if len(args) == 7:
            arg_names = cls._args[0:1] + cls._args[2:]
        else:
            arg_names = cls._args

        kwargs = {kw[0]: v for kw, v in zip(arg_names, args)}

        entry = cls(comment=comment, **kwargs)

        return entry


class BondtypesEntry(P2TermEntry):
    _node_key_name = "bondtypes_entry"


class AngletypesEntry(P3TermEntry):
    _node_key_name = "angletypes_entry"


class PairtypesEntry(P2TermEntry):
    _node_key_name = "pairtypes_entry"


class DihedraltypesEntry(P4TermEntry):
    _node_key_name = "dihedraltypes_entry"


class ConstrainttypesEntry(P2TermEntry):
    _node_key_name = "constrainttypes_entry"


class NonbondedParamsEntry(P2TermEntry):
    _node_key_name = "nonbonded_params_entry"


class MoleculetypeEntry(SectionEntry):
    _node_key_name = "moleculetype_entry"
    _args = [
        ("molecule", str, make_formatter("")),
        ("nrexcl", int, make_formatter(">5")),
    ]

    def __init__(self, molecule=None, nrexcl=None, comment=None):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)


class SystemEntry(SectionEntry):
    _node_key_name = "system_entry"
    _args = [("name", str, make_formatter(""))]

    def __init__(self, name=None, comment=None):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)

    @classmethod
    def from_line(cls, *args, comment):
        entry = cls(
            name=" ".join(args),
            comment=comment,
        )

        return entry


class MoleculesEntry(SectionEntry):
    _node_key_name = "molecules_entry"
    _args = [
        ("molecule", str, make_formatter("")),
        ("number", int, make_formatter(">6")),
    ]

    def __init__(self, molecule=None, number=None, comment=None):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)


class AtomsEntry(SectionEntry):
    _node_key_name = "atoms_entry"
    _args = [
        ("nr", int, make_formatter("<5")),
        ("type", str, make_formatter("<5")),
        ("resnr", int, make_formatter("<5")),
        ("residue", str, make_formatter("<5")),
        ("atom", str, make_formatter("<5")),
        ("cgnr", int, make_formatter("<5")),
        ("charge", float, make_formatter(">7.4f")),
        ("mass", float, make_formatter("7.3f")),
        ("typeB", float, make_formatter("<5")),
        ("chargeB", float, make_formatter(">7.4f")),
        ("massB", float, make_formatter("7.3f")),
    ]

    def __init__(
        self,
        nr=None,
        type=None,
        resnr=None,
        residue=None,
        atom=None,
        cgnr=None,
        charge=None,
        mass=None,
        typeB=None,
        chargeB=None,
        massB=None,
        comment=None,
    ):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)


class BondsEntry(P2TermEntry):
    _node_key_name = "bonds_entry"


class PairsEntry(P2TermEntry):
    _node_key_name = "pairs_entry"


class PairsNBEntry(P2TermEntry):
    _node_key_name = "pairs_nb_entry"


class AnglesEntry(P3TermEntry):
    _node_key_name = "angles_entry"


class DihedralsEntry(P4TermEntry):
    _node_key_name = "dihedrals_entry"


class ExclusionsEntry(SectionEntry):
    _node_key_name = "exclusions_entry"
    _args = [("indices", None, make_formatter(">5"))]

    def __init__(self, indices=None, comment=None):
        locals_ = trim_locals(locals())

        super().__init__(**locals_)

        if indices is None:
            indices = []
        self.indices = [int(i) for i in indices]

    @classmethod
    def from_line(cls, *args, comment):
        entry = cls(
            indices=args,
            comment=comment,
        )

        return entry


class ConstraintsEntry(P2TermEntry):
    _node_key_name = "constraints_entry"


class SettlesEntry(P1TermEntry):
    _node_key_name = "settles_entry"


class VirtualSites1Entry(P1TermEntry):
    _node_key_name = "virtual_sites1_entry"
    _args = [
        ("i", int, make_formatter(">5")),
        ("f", None, make_formatter(">5")),
        ("funct", int, make_formatter(">5")),
        ("c", None, make_formatter("1.6e")),
    ]

    def __init__(self, i=None, f=None, funct=None, c=None, comment=None):
        super().__init__(i=i, funct=funct, c=c, comment=comment)

        if f is None:
            f = []
        self.f = [int(x) for x in f]

    @classmethod
    def from_line(cls, *args, comment=None):
        i, f1, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None
        f = [f1]

        entry = cls(
            i=i,
            f=f,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class VirtualSites2Entry(VirtualSites1Entry):
    _node_key_name = "virtual_sites2_entry"

    @classmethod
    def from_line(cls, *args, comment=None):
        i, f1, f2, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None
        f = [f1, f2]

        entry = cls(
            i=i,
            f=f,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class VirtualSites3Entry(VirtualSites1Entry):
    _node_key_name = "virtual_sites3_entry"

    @classmethod
    def from_line(cls, *args, comment=None):
        i, f1, f2, f3, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None
        f = [f1, f2, f3]

        entry = cls(
            i=i,
            f=f,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class VirtualSites4Entry(VirtualSites1Entry):
    _node_key_name = "virtual_sites4_entry"

    @classmethod
    def from_line(cls, *args, comment=None):
        i, f1, f2, f3, f4, *rest = args
        if rest:
            funct, *c = rest
        else:
            funct = c = None
        f = [f1, f2, f3, f4]

        entry = cls(
            i=i,
            f=f,
            funct=funct,
            c=c,
            comment=comment,
        )

        return entry


class VirtualSitesNEntry(VirtualSites1Entry):
    _node_key_name = "virtual_sitesn_entry"
    _args = [
        ("i", int, make_formatter(">5")),
        ("funct", int, make_formatter(">5")),
        ("f", None, make_formatter(">5")),
    ]

    def __init__(self, i=None, funct=None, f=None, comment=None):
        super().__init__(i=i, funct=funct, f=f, comment=comment)

        delattr(self, "c")

    @classmethod
    def from_line(cls, *args, comment=None):
        i, *rest = args
        if rest:
            funct, *f = rest
        else:
            funct = f = None

        entry = cls(
            i=i,
            f=f,
            funct=funct,
            comment=comment,
        )

        return entry


class PositionRestraintsEntry(P1TermEntry):
    _node_key_name = "position_restraints_entry"


class DistanceRestraintsEntry(P2TermEntry):
    _node_key_name = "distance_restraints_entry"


class DihedralRestraintsEntry(P4TermEntry):
    _node_key_name = "dihedral_restraints_entry"


class OrientationRestraintsEntry(P2TermEntry):
    _node_key_name = "orientations_restraints_entry"


class AngleRestraintsEntry(P4TermEntry):
    _node_key_name = "angle_restraints_entry"


class AngleRestraintsZEntry(P2TermEntry):
    _node_key_name = "angle_restraints_z_entry"
