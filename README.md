[![Code Coverage](https://raw.githubusercontent.com/janjoswig/MDParser/master/badges/coverage.svg)](https://github.com/janjoswig/MDParser)


# MDParser

This is a package for Python-parsers to process typical file formats used for Molecular Dynamics simulations. Currently supported modules and highlights:

## Topologies (`mdparser.topology`)

### GROMACS (`GromacsTopParser`)

Read GROMACS topology (.top) files and image them as a Python object or vice versa. The structure of the file is essentially captured in a doubly-linked list exposing it for easy manipulation. Common tasks like adding parts to a topology, merging topologies, retrieval of information, or checking the file for consistency can be performed.
