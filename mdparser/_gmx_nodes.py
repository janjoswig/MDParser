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
        """Default representation"""
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
    _args = []

    def __init__(self, comment=None):
        super().__init__()

        self.comment = comment
        self._raw = None

    def __copy__(self):
        kwargs = {
            arg_name: getattr(self, arg_name)
            for arg_name
            in self._args
        }
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

        kwargs = {
            kw: v
            for kw, v
            in zip(cls._args, args)
            }

        entry = cls(
            comment=comment,
            **kwargs
        )

        return entry

    def __str__(self):
        if self._raw is not None:
            return self._raw

        return_str = ""
        return_str = self._finish_str(return_str)

        return return_str

    def __repr__(self):
        arg_name_repr = ", ".join(
            f"{arg_name!s}={getattr(self, arg_name)!r}"
            for arg_name in self._args
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


class P2TermEntry(SectionEntry, PropertyInvoker):

    _node_key_name = "p2_term_entry"

    _args = [
        "i", "j",
        "funct",
        "c"
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

    def __init__(
            self,
            i=None, j=None,
            funct=None,
            c=None,
            comment=None):

        super().__init__(comment=comment)

        if i is not None:
            i = int(i)
        self.i = i

        if j is not None:
            j = int(j)
        self.j = j

        if funct is not None:
            funct = int(funct)
        self.funct = funct

        if c is None:
            c = []
        self.c = [float(x) for x in c]

        for index in range(len(c)):
            setattr(
                self, f"c{index}", property(
                    fget=self.getc(index),
                    fset=self.setc(index),
                    fdel=self.delc(index),
                    doc="Access term coefficients"
                    )
                )

    @classmethod
    def from_line(cls, *args, comment=None):

        i, j, funct, *c = args

        entry = cls(
            i=i, j=j, funct=funct, c=c,
            comment=comment,
        )

        return entry

    def __str__(self):
        return_str = ""

        if self.i is not None:
            return_str += f"{self.i:>5}"

        if self.j is not None:
            return_str += f" {self.j:>5}"

        if self.funct is not None:
            return_str += f" {self.funct:>5}"

        for x in self.c:
            if x is not None:
                return_str += f" {x:1.6e}"

        return_str = self._finish_str(return_str)

        return return_str


class DefaultsEntry(SectionEntry):
    """Entry in defaults section"""

    _node_key_name = "defaults_entry"
    _args = [
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

        return_str = self._finish_str(return_str)

        return return_str


class AtomtypesEntry(SectionEntry):

    _node_key_name = "atomtypes_entry"
    _args = [
        "name",
        "bond_type",
        "at_num",
        "mass",
        "charge",
        "ptype",
        "sigma",
        "epsilon"
    ]

    def __init__(
            self, name=None, bond_type=None, at_num=None, mass=None,
            charge=None, ptype=None, sigma=None, epsilon=None, comment=None):

        super().__init__(comment=comment)

        self.name = name
        self.bond_type = bond_type

        if at_num is not None:
            self.at_num = int(at_num)

        if mass is not None:
            self.mass = float(mass)

        if charge is not None:
            self.charge = float(charge)

        self.ptype = ptype

        if sigma is not None:
            self.sigma = float(sigma)

        if epsilon is not None:
            self.epsilon = float(epsilon)

        self.comment = comment

    @classmethod
    def from_line(cls, *args, comment):
        if len(args) == 7:
            arg_names = cls._args[0:1] + cls._args[2:]
        else:
            arg_names = cls._args

        kwargs = {
            kw: v
            for kw, v
            in zip(arg_names, args)
            }

        entry = cls(
            comment=comment,
            **kwargs
        )

        return entry

    def __str__(self):
        return_str = ""
        if self.name is not None:
            return_str += f"{self.name:<9}"

        if self.bond_type is not None:
            return_str += f" {self.bond_type:<4}"

        if self.at_num is not None:
            return_str += f" {self.at_num:<3}"

        if self.mass is not None:
            return_str += f" {self.mass:<8}"

        if self.charge is not None:
            return_str += f" {self.charge:<6}"

        if self.ptype is not None:
            return_str += f" {self.ptype:<1}"

        if self.sigma is not None:
            return_str += f" {self.sigma:1.5e}"

        if self.epsilon is not None:
            return_str += f"  {self.epsilon:1.5e}"

        return_str = self._finish_str(return_str)

        return return_str

    def __repr__(self):
        arg_name_repr = ", ".join(
            f"{arg_name!s}={getattr(self, arg_name)!r}"
            for arg_name in self._args
            )

        return f"{type(self).__name__}({arg_name_repr})"


class BondtypesEntry(P2TermEntry):
    _node_key_name = "bondtypes_entry"


class AngletypesEntry(SectionEntry):
    _node_key_name = "angletypes_entry"
    _args = [
        "i", "j", "k", "func", "c0", "c1", "c2", "c3"
    ]


class PairtypesEntry(P2TermEntry):
    _node_key_name = "pairtypes_entry"


class DihedraltypesEntry(SectionEntry):
    _node_key_name = "dihedraltypes_entry"
    _args = [
        "i", "j", "k", "l", "func", "c0", "c1", "c2", "c3", "c4", "c5"
    ]


class ConstrainttypesEntry(SectionEntry):
    _node_key_name = "constrainttypes_entry"
    _args = [
        "i", "j", "func", "c0", "c1"
    ]


class NonbondedParamsEntry(SectionEntry):
    _node_key_name = "nonbonded_params_entry"
    _args = [
        "i", "j", "func", "c0", "c1", "c2"
    ]


class MoleculetypeEntry(SectionEntry):

    _node_key_name = "moleculetype_entry"
    _args = [
        "molecule", "nrexcl"
    ]

    def __init__(self, molecule=None, nrexcl=None, comment=None):

        super().__init__(comment=comment)

        self.molecule = molecule

        if nrexcl is not None:
            nrexcl = int(nrexcl)
        self.nrexcl = nrexcl

    def __str__(self):
        return_str = ""

        if self.molecule is not None:
            return_str += f"{self.molecule}"

        if self.nrexcl is not None:
            return_str += f"    {self.nrexcl}"

        return_str = self._finish_str(return_str)

        return return_str


class SystemEntry(SectionEntry):

    _node_key_name = "system_entry"
    _args = [
        "name"
    ]

    def __init__(self, name=None, comment=None):

        super().__init__(comment=comment)

        self.name = name

    @classmethod
    def from_line(cls, *args, comment):

        entry = cls(
            name=" ".join(args),
            comment=comment,
        )

        return entry

    def __str__(self):
        return_str = ""

        if self.name is not None:
            return_str += f"{self.name}"

        return_str = self._finish_str(return_str)

        return return_str


class MoleculesEntry(SectionEntry):

    _node_key_name = "molecules_entry"
    _args = [
        "molecule", "number"
    ]

    def __init__(self, molecule=None, number=None, comment=None):

        super().__init__(comment=comment)

        self.molecule = molecule

        if number is not None:
            number = int(number)
        self.number = number

    def __str__(self):
        return_str = ""

        if self.molecule is not None:
            return_str += f"{self.molecule}"

        if self.number is not None:
            return_str += f"    {self.number}"

        return_str = self._finish_str(return_str)

        return return_str


class AtomsEntry(SectionEntry):

    _node_key_name = "atoms_entry"
    _args = [
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
        return_str = ""

        if self.nr is not None:
            return_str += f"{self.nr:<5}"

        if self.type is not None:
            return_str += f" {self.type:<5}"

        if self.resnr is not None:
            return_str += f" {self.resnr:<5}"

        if self.residue is not None:
            return_str += f" {self.residue:<5}"

        if self.atom is not None:
            return_str += f" {self.atom:<5}"

        if self.cgnr is not None:
            return_str += f" {self.cgnr:<5}"

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

        return_str = self._finish_str(return_str)

        return return_str



class BondsEntry(P2TermEntry):

    _node_key_name = "bonds_entry"


class PairsEntry(P2TermEntry):

    _node_key_name = "pairs_entry"


class PairsNBEntry(P2TermEntry):

    _node_key_name = "pairs_nb_entry"


class ExclusionsEntry(SectionEntry):

    _node_key_name = "exclusions_entry"

    _args = [
        "indices"
        ]

    def __init__(
            self,
            indices=None,
            comment=None):

        super().__init__(comment=comment)

        if indices is not None:
            indices = [int(i) for i in indices]
        self.indices = indices

    @classmethod
    def from_line(cls, *args, comment):

        entry = cls(
            indices=args,
            comment=comment,
        )

        return entry

    def __str__(self):
        return_str = ""

        if self.indices is not None:
            return_str += " ".join([f"{i:>5}" for i in self.indices])

        return_str = self._finish_str(return_str)

        return return_str


class ConstraintsEntry(P2TermEntry):

    _node_key_name = "constraints_entry"