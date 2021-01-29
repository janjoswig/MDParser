from abc import ABC, abstractmethod


class NodeValue(ABC):
    """Abstract base class for node value types"""

    _count = 0
    _node_key_name = "abstract"

    @classmethod
    def reset_count(cls, value: int = None):
        if value is None:
            value = 0
        cls._count = value

    @classmethod
    def increase_count(cls):
        cls._count += 1

    @property
    def count(self):
        return self._count

    def __init__(self):
        self.increase_count()
        self._count = type(self)._count

    @abstractmethod
    def __str__(self):
        """Return node content formatted for topology file"""

    def __repr__(self):
        return f"{type(self).__name__}()"

    def _make_node_key(self) -> str:
        """Return string usable as node key"""
        return f"{self._node_key_name}_{self._count}"


class GenericNodeValue(NodeValue):
    """Generic fallback node value"""

    _node_key_name = "generic"

    def __init__(self, value):
        super().__init__()
        self.value = value

    def __str__(self):
        return self.value.__str__()

    def __repr__(self):
        return f"{type(self).__name__}(value={self.value!r})"


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


class SectionEntry(NodeValue):
    """A section entry"""

    _node_key_name = "section_entry"
    _arg_names = []

    def __init__(self, comment=None):
        super().__init__()

        self.comment = comment

    @classmethod
    def from_line(cls, *args, comment=None):

        kwargs = {
            kw: v
            for kw, v
            in zip(cls._arg_names, args)
            }

        entry = cls(
            comment=comment,
            **kwargs
        )

        return entry


class DefaultsEntry(SectionEntry):
    """Entry in defaults section"""

    _node_key_name = "defaults_entry"
    _arg_names = [
        "nbfunc", "comb_rule",
        "gen_pairs", "fudgeLJ", "fudgeQQ",
        "n"
    ]

    def __init__(
            self,
            nbfunc=None, comb_rule=None,
            gen_pairs="no", fudgeLJ=None, fudgeQQ=None, n=None,
            comment=None):

        super().__init__(comment=comment)

        if nbfunc is not None:
            nbfunc = int(nbfunc)
        self.nbfunc = nbfunc

        if comb_rule is not None:
            comb_rule = int(comb_rule)
        self.comb_rule = comb_rule

        self.gen_pairs = gen_pairs

        if fudgeLJ is not None:
            fudgeLJ = float(fudgeLJ)
        self.fudgeLJ = fudgeLJ

        if fudgeQQ is not None:
            fudgeQQ = float(fudgeQQ)
        self.fudgeQQ = fudgeQQ

        if n is not None:
            n = int(n)
        self.n = n

    def __str__(self):
        return_str = ""

        if self.nbfunc is not None:
            return_str += f"{self.nbfunc:<15}"

        if self.comb_rule is not None:
            return_str += f" {self.comb_rule:<15}"

        if self.gen_pairs is not None:
            return_str += f" {self.gen_pairs:<15}"

        if self.fudgeLJ is not None:
            return_str += f" {self.fudgeLJ:<7}"

        if self.fudgeQQ is not None:
            return_str += f" {self.fudgeQQ:<7}"

        if self.n is not None:
            return_str += f" {self.n:<7}"

        if self.comment is not None:
            return_str += f" ; {self.comment}"

        return return_str


class AtomtypesEntry(SectionEntry):

    _node_key_name = "atomtypes_entry"

    def __init__(self, *args, comment=None):

        super().__init__()

        self.name = args[0]
        self.at_num = int(args[-6])
        self.mass = float(args[-5])
        self.charge = float(args[-4])
        self.ptype = args[-3]
        self.sigma = float(args[-2])
        self.epsilon = float(args[-1])

        if len(args) == 8:
            self.bond_type = args[1]
        else:
            self.bond_type = None

        self.comment = comment

    def __str__(self):
        return_str = f"{self.name:<9} "
        if self.bond_type is not None:
            return_str += f"{self.bond_type:<4} "
        return_str += f"{self.at_num:<3} "
        return_str += f"{self.mass:<8} "
        return_str += f"{self.charge:<6} "
        return_str += f"{self.ptype:<1} "
        return_str += f"{self.sigma:1.5e}  "
        return_str += f"{self.epsilon:1.5e} "
        if self.comment is not None:
            return_str += f"; {self.comment}"
        return return_str


class MoleculetypeEntry(SectionEntry):

    _node_key_name = "moleculetype_entry"
    _arg_names = [
        "name", "nrexcl"
    ]

    def __init__(self, name=None, nrexcl=None, comment=None):

        super().__init__(comment=comment)

        self.name = name

        if nrexcl is not None:
            nrexcl = int(nrexcl)
        self.nrexcl = nrexcl

    def __str__(self):
        return_str = ""

        if self.name is None:
            return_str += f"{self.name}"

        if self.nrexcl is not None:
            return_str += f"    {self.nrexcl}"

        if self.comment is not None:
            return_str += f" ; {self.comment}"

        return return_str


class AtomsEntry(SectionEntry):

    _node_key_name = "atoms_entry"
    _arg_names = [
        "nr", "type", "resnr", "residue",
        "atom", "cgnr", "charge", "mass",
        "typeB", "chargeB", "massB"
        ]

    def __init__(
            self,
            nr=None, type=None, resnr=None, residue=None,
            atom=None, cgnr=None, charge=None, mass=None,
            typeB=None, chargeB=None, massB=None,
            comment=None):

        super().__init__(comment=comment)

        if nr is not None:
            nr = int(nr)
        self.nr = nr

        self.type = type

        if resnr is not None:
            resnr = int(resnr)
        self.resnr = resnr

        self.residue = residue
        self.atom = atom

        if cgnr is not None:
            cgnr = int(cgnr)
        self.cgnr = cgnr

        if charge is not None:
            charge = float(charge)
        self.charge = charge

        if mass is not None:
            mass = float(mass)
        self.mass = mass

        self.typeB = typeB

        if chargeB is not None:
            chargeB = float(chargeB)
        self.chargeB = chargeB

        if massB is not None:
            massB = float(massB)
        self.massB = massB

    def __str__(self):
        return_str = (
            f" {self.nr:<5}"
            f" {self.type:<5}"
            f" {self.resnr:<5}"
            f" {self.residue:<5}"
            f" {self.atom:<5}"
            f"{self.cgnr:<5}"
        )

        if self.charge is not None:
            return_str += f" {self.charge:<6}"

        if self.mass is not None:
            return_str += f" {self.mass:<6}"

        if self.typeB is not None:
            return_str += f" {self.typeB:<5}"

        if self.chargeB is not None:
            return_str += f" {self.chargeB:<6}"

        if self.massB is not None:
            return_str += f" {self.massB:<6}"

        if self.comment is not None:
            return_str += f" ; {self.comment}"

        return return_str


class BondsEntry(SectionEntry):

    _node_key_name = "bonds_entry"

    _arg_names = [
        "ai", "aj", "funct",
        "c0", "c1", "c2", "c3",
        ]

    def __init__(
            self,
            ai=None, aj=None,
            funct=None,
            c0=None,
            c1=None,
            c2=None,
            c3=None,
            comment=None):

        super().__init__(comment=comment)

        if ai is not None:
            ai = int(ai)
        self.ai = ai

        if aj is not None:
            aj = int(aj)
        self.aj = aj

        if funct is not None:
            funct = int(funct)
        self.funct = funct

        if c0 is not None:
            c0 = float(c0)
        self.c0 = c0

        if c1 is not None:
            c1 = float(c1)
        self.c1 = c1

        if c2 is not None:
            c2 = float(c2)
        self.c2 = c2

        if c3 is not None:
            c3 = float(c3)
        self.c3 = c3

    def __str__(self):
        return_str = ""

        if self.ai is not None:
            return_str += f"{self.ai:>5}"

        if self.aj is not None:
            return_str += f" {self.aj:>5}"

        if self.funct is not None:
            return_str += f" {self.funct:>5}"

        if self.c0 is not None:
            return_str += f" {self.c0:>5}"

        if self.c1 is not None:
            return_str += f" {self.c1:>5}"

        if self.c2 is not None:
            return_str += f" {self.c2:>5}"

        if self.c3 is not None:
            return_str += f" {self.c3:>5}"

        if self.comment is not None:
            return_str += f" ; {self.comment}"

        return return_str
