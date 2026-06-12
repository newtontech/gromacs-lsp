# Upstream GROMACS Reference Links (GROMACS 上游参考链接)

**Purpose**: Concise manifest of official GROMACS documentation sources for LLM wiki evidence.
**Do not duplicate content**; link to canonical upstream resources.

## GROMACS Manual

| Resource | URL | Description |
|----------|-----|-------------|
| GROMACS Manual (current) | https://manual.gromacs.org/current/ | Full reference manual |
| User Guide | https://manual.gromacs.org/current/user-guide/index.html | How-to guides and workflows |
| Reference Manual | https://manual.gromacs.org/current/reference-manual/index.html | Algorithms and theory |
| Release Notes | https://manual.gromacs.org/current/release-notes/index.html | Version changelog |

## File Format Documentation

| Format | URL | Scope |
|--------|-----|-------|
| Topology File (.top/.itp) | https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html | Complete topology format reference |
| MDP Parameters | https://manual.gromacs.org/current/user-guide/mdp-options.html | All .mdp run parameter options |
| Coordinate File (.gro) | https://manual.gromacs.org/current/reference-manual/file-formats.html#gro | GROMOS87 coordinate format |
| Trajectory Files (.xtc/.trr/.tng) | https://manual.gromacs.org/current/reference-manual/file-formats.html | Trajectory formats |
| Energy File (.edr) | https://manual.gromacs.org/current/reference-manual/file-formats.html#edr | Energy data format |
| Index File (.ndx) | https://manual.gromacs.org/current/user-guide/file-formats.html | Atom group index files |

## Key Algorithm Pages

| Topic | URL | Description |
|-------|-----|-------------|
| Electrostatics (PME) | https://manual.gromacs.org/current/reference-manual/special/electrostatics.html | PME and other electrostatics |
| Thermostats | https://manual.gromacs.org/current/reference-manual/algorithms/molecular-dynamics.html#thermostats | Temperature coupling methods |
| Barostats | https://manual.gromacs.org/current/reference-manual/algorithms/molecular-dynamics.html#pressure-coupling | Pressure coupling methods |
| Constraints | https://manual.gromacs.org/current/reference-manual/algorithms/constraints.html | LINCS, SHAKE, SETTLE |
| Free Energy | https://manual.gromacs.org/current/user-guide/terminology.html#free-energy | Free energy calculations |
| Replica Exchange | https://manual.gromacs.org/current/user-guide/terminology.html#replica-exchange | REMD methods |
| Enhanced Sampling (AWH) | https://manual.gromacs.org/current/user-guide/mdp-options/awh.html | Accelerated Weight Histogram |
| Pull Code | https://manual.gromacs.org/current/user-guide/mdp-options/pull.html | Umbrella sampling / SMD |

## Tutorials

| Tutorial | URL | Notes |
|----------|-----|-------|
| GROMACS Tutorials (Justin Lemkul) | http://www.mdtutorials.com/gmx/ | Comprehensive step-by-step guides |
| Lysozyme in Water | http://www.mdtutorials.com/gmx/lysozyme/index.html | Classic introductory tutorial |
| Membrane Protein | http://www.mdtutorials.com/gmx/membrane_protein/index.html | Membrane protein simulation |
| Protein-Ligand Complex | http://www.mdtutorials.com/gmx/complex/index.html | Ligand binding simulation |
| GROMACS Official Tutorials | https://tutorials.gromacs.org/ | Official tutorial collection |

## Force Fields

| Force Field | URL | Notes |
|-------------|-----|-------|
| OPLS-AA | https://manual.gromacs.org/current/user-guide/force-fields.html | Optimized Potentials for Liquid Simulations |
| AMBER | https://manual.gromacs.org/current/user-guide/force-fields.html | Assisted Model Building with Energy Refinement |
| CHARMM | https://manual.gromacs.org/current/user-guide/force-fields.html | Chemistry at HARvard Macromolecular Mechanics |
| GROMOS | https://manual.gromacs.org/current/user-guide/force-fields.html | GROningen MOlecular Simulation |

## Developer / Source

| Resource | URL | Notes |
|----------|-----|-------|
| GROMACS GitLab | https://gitlab.com/gromacs/gromacs | Official source repository |
| MDParser | https://github.com/janjoswig/MDParser | Topology parser library |

---
*Manifest created: 2026-06-13*
*Evidence for issue #27: upstream documentation coverage gap fill*
