# GROMACS Analysis Tools Reference

> Source: https://manual.gromacs.org/current/user-guide/cmdline.html
> Captured: 2026-06-12

Complete list of `gmx` analysis and utility tools from GROMACS 2026.2.

## Structure Analysis

- `gmx rms` — Calculate RMSD between structures
- `gmx rmsf` — Calculate root mean square fluctuation per atom
- `gmx rmsdist` — Calculate RMSD from pairwise distances
- `gmx gyrate` — Calculate radius of gyration
- `gmx gyrate-legacy` — Legacy radius of gyration calculation
- `gmx sasa` — Calculate solvent accessible surface area
- `gmx distance` — Calculate distances between pairs
- `gmx gangle` — Calculate angles and dihedrals
- `gmx mindist` — Calculate minimum distances between groups
- `gmx pairdist` — Calculate pairwise distance distributions
- `gmx confrms` — Confront two structures by fitting

## Trajectory Analysis

- `gmx traj` — Output coordinates, velocities, forces from trajectory
- `gmx trajectory` — Write subset of trajectory to output
- `gmx trjconv` — Convert and process trajectory files
- `gmx trjcat` — Concatenate trajectory files
- `gmx trjorder` — Order molecules in trajectory
- `gmx filter` — Frequency filter trajectory
- `gmx convert-trj` — Convert trajectory formats

## Energy Analysis

- `gmx energy` — Extract energy components from .edr file
- `gmx eneconv` — Convert energy files
- `gmx enemat` — Extract energy matrix from energy file

## Radial Distribution Functions

- `gmx rdf` — Calculate radial distribution functions
- `gmx sorient` — Solvent orientation analysis

## Correlation Functions

- `gmx msd` — Calculate mean square displacement
- `gmx velacc` — Calculate velocity autocorrelation function
- `gmx rotacf` — Calculate rotational autocorrelation function
- `gmx tcaf` — Calculate translational current autocorrelation
- `gmx vanhove` — Calculate van Hove displacement function
- `gmx analyze` — Analyze and plot data

## Covariance / PCA Analysis

- `gmx covar` — Calculate covariance matrix
- `gmx anaeig` — Analyze eigenvectors and eigenvalues
- `gmx nmeig` — Diagonalize Hessian matrix
- `gmx nmens` — Generate ensemble from normal modes
- `gmx nmtraj` — Generate trajectory from normal modes
- `gmx nmr` — Analyze NMR data

## Hydrogen Bonds

- `gmx hbond` — Compute and analyze hydrogen bonds
- `gmx hbond-legacy` — Legacy hydrogen bond analysis

## Protein-specific Analysis

- `gmx dssp` — Assign secondary structure (DSSP)
- `gmx rama` — Calculate Ramachandran plots
- `gmx chi` — Calculate chi (dihedral) angles
- `gmx helix` — Analyze helix properties
- `gmx helixorient` — Calculate helix orientation
- `gmx wheel` — Generate helical wheel plot
- `gmx saltbr` — Analyze salt bridges
- `gmx polystat` — Analyze polymer properties

## Clustering

- `gmx cluster` — Cluster structures
- `gmx clustsize` — Calculate cluster size distribution
- `gmx extract-cluster` — Extract frames from clusters

## Density and Order

- `gmx density` — Calculate densities
- `gmx densmap` — Calculate 2D density maps
- `gmx densorder` — Calculate density order parameters
- `gmx h2order` — Calculate water orientation order
- `gmx hydorder` — Calculate hydrogen bond order
- `gmx order` — Calculate order parameters for lipids

## Electrostatic / Dielectric

- `gmx potential` — Calculate electrostatic potential
- `gmx dielectric` — Calculate frequency-dependent dielectric constant
- `gmx dipoles` — Calculate dipole autocorrelation

## Thermodynamic / Free Energy

- `gmx bar` — Bennett acceptance ratio for free energies
- `gmx wham` — Weighted histogram analysis after umbrella sampling
- `gmx awh` — Extract AWH data (PMF, bias, target)
- `gmx sham` — Calculate 2D free energy landscapes (Sham)
- `gmx lie` — Linear interaction energy for binding free energies

## System Preparation

- `gmx pdb2gmx` — Convert PDB to GROMACS topology
- `gmx editconf` — Edit box and coordinates
- `gmx solvate` — Add solvent molecules
- `gmx genion` — Add ions to system
- `gmx genrestr` — Generate position restraint files
- `gmx genconf` — Generate configuration
- `gmx insert-molecules` — Insert molecules into system
- `gmx make_ndx` — Create or modify index files
- `gmx select` — Select atoms/groups with query language
- `gmx x2top` — Generate primitive topology from coordinates

## Simulation Running

- `gmx grompp` — Preprocess run input files
- `gmx mdrun` — Run molecular dynamics simulation
- `gmx convert-tpr` — Modify run input files
- `gmx tune_pme` — Optimize PME settings
- `gmx pme_error` — Estimate PME error

## Other Tools

- `gmx check` — Check consistency of files
- `gmx dump` — Human-readable dump of run input file
- `gmx dos` — Calculate density of states
- `gmx mdmat` — Calculate distance matrices
- `gmx sigeps` — Convert C6/C12 to sigma/epsilon
- `gmx xpm2ps` — Convert XPM matrices to PostScript
- `gmx report-methods` — Report simulation methods used
- `gmx spatial` — Calculate spatial distribution function
- `gmx spol` — Analyze solvent polarization
- `gmx dyecoupl` — Analyze dye coupling
- `gmx disre` — Analyze distance restraints
- `gmx current` — Calculate current autocorrelation
- `gmx freevolume` — Calculate free volume
- `gmx scattering` — Calculate scattering curves
- `gmx sans-legacy` — Legacy SANS calculation
- `gmx saxs-legacy` — Legacy SAXS calculation
- `gmx nonbonded-benchmark` — Benchmark non-bonded performance
- `gmx principal` — Calculate principal axes
- `gmx mk_angndx` — Generate angle index file
- `gmx make_edi` — Generate essential dynamics input
- `gmx help` — Display help information

## Default Groups (auto-generated)

When no index file is supplied, these groups are available:
- `System` — all atoms
- `Protein` — protein atoms
- `Protein-H` — protein without hydrogens
- `C-alpha` — alpha carbons
- `Backbone` — N, Ca, C
- `MainChain` — N, Ca, C, O
- `MainChain+Cb` — including C-beta
- `MainChain+H` — including backbone H
- `SideChain` — sidechain atoms
- `SideChain-H` — sidechain without hydrogens
- `Non-Protein` — non-protein atoms
- `DNA`, `RNA` — nucleic acid atoms
- `Water` — water molecules (SOL, WAT, HOH, etc.)
- `non-Water` — non-water atoms
- `Ion` — ion atoms
- `Water_and_Ions` — combined water and ions
- `Other` — atoms not protein/DNA/RNA

## Dynamic Selections

Modern tools support text-based selections similar to VMD:
- `resname ABC` — select by residue name
- `within 2 of resname DEF` — geometric criteria
- Selections can be dynamic (different atoms per frame)
- Use `gmx select` to test selections
- Interactive help: type `help` in selection prompt
