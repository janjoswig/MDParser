import pytest

from mdparser import _gmx_nodes, topology


@pytest.fixture
def tasks_top():
    top = topology.GromacsTopology()

    top.add("ff", _gmx_nodes.Include("forcefield.itp"))
    top.add("mol1", _gmx_nodes.MoleculetypeSection())
    top.add("mol1_entry", _gmx_nodes.MoleculetypeEntry("mol1", 3))
    top.add("mol1_atoms", _gmx_nodes.AtomsSubsection())
    top.add("mol1_atoms_entry_1", _gmx_nodes.AtomsEntry(nr=1, type="A"))
    top.add("mol1_atoms_entry_2", _gmx_nodes.AtomsEntry(nr=2, type="B"))
    top.add("mol1_bonds", _gmx_nodes.BondsSubsection())
    top.add("mol1_bonds_entry_1", _gmx_nodes.BondsEntry(i=1, j=2, funct=1))
    top.add("mol2", _gmx_nodes.MoleculetypeSection())
    top.add("mol2_entry", _gmx_nodes.MoleculetypeEntry("mol2", 3))
    top.add("mol2_atoms", _gmx_nodes.AtomsSubsection())
    top.add("mol2_atoms_entry_1", _gmx_nodes.AtomsEntry(nr=1, type="C"))
    top.add("system", _gmx_nodes.SystemSection())
    top.add("system_entry", _gmx_nodes.SystemEntry("Two molecules"))
    top.add("molecules", _gmx_nodes.MoleculesSection())
    top.add("mol1count", _gmx_nodes.MoleculesEntry("mol1", 2))
    top.add("mol2count", _gmx_nodes.MoleculesEntry("mol2", 2))

    return top
