"""Hover documentation for GROMACS file formats."""
from __future__ import annotations

from typing import Optional

# -- MDP key documentation --------------------------------------------------

_MDP_DOCS: dict[str, str] = {
    "integrator": (
        "Integration method.\n"
        "Values: md (molecular dynamics), steep (steepest descent minimization), "
        "cg (conjugate gradient minimization), l-bfgs, md-vv, md-vv-avek, "
        "nm (normal mode analysis), tpi, tpic, mimic, bending, "
        " umbrella-integration."
    ),
    "nsteps": (
        "Total number of steps to integrate.\n"
        "Type: integer (must be >= 0)."
    ),
    "dt": (
        "Time step for integration (ps).\n"
        "Type: float. Common values: 0.001-0.002."
    ),
    "nstxout": (
        "Number of steps between writing coordinates to the output trajectory file (.trr/.xtc).\n"
        "Type: integer. 0 disables coordinate output."
    ),
    "nstvout": (
        "Number of steps between writing velocities to the output trajectory.\n"
        "Type: integer. 0 disables velocity output."
    ),
    "nstenergy": (
        "Number of steps between writing energies to the energy file (.edr).\n"
        "Type: integer. 0 disables energy output."
    ),
    "nstlog": (
        "Number of steps between writing to the log file.\n"
        "Type: integer. 0 disables log output."
    ),
    "cutoff-scheme": (
        "Cutoff scheme for non-bonded interactions.\n"
        "Values: verlet (group is deprecated)."
    ),
    "coulombtype": (
        "Electrostatics method.\n"
        "Values: PME, PME-Switch, PME-User, Ewald, Reaction-Field, "
        "Cut-off, Shift, User, Generic, Reply."
    ),
    "rcoulomb": (
        "Distance (nm) for Coulomb cutoff.\n"
        "Type: float."
    ),
    "rvdw": (
        "Distance (nm) for Van der Waals cutoff.\n"
        "Type: float."
    ),
    "constraints": (
        "Which bonds to constrain.\n"
        "Values: none, all-bonds, h-bonds, all-angles."
    ),
    "constraint-algorithm": (
        "Algorithm for constraints.\n"
        "Values: lincs, shake."
    ),
    "tcoupl": (
        "Temperature coupling method.\n"
        "Values: no, berendsen, nose-hoover, andersen, v-rescale."
    ),
    "pcoupl": (
        "Pressure coupling method.\n"
        "Values: no, berendsen, parrinello-rahman, mttk, c-rescale."
    ),
    "ref-t": (
        "Reference temperature (K) for temperature coupling groups.\n"
        "Type: float or list of floats."
    ),
    "ref-p": (
        "Reference pressure (bar) for pressure coupling.\n"
        "Type: float or list of floats."
    ),
    "gen-vel": (
        "Generate velocities from a Maxwell distribution at start.\n"
        "Values: yes, no."
    ),
    "pbc": (
        "Periodic boundary conditions.\n"
        "Values: xyz, no, xy, xz, yz, x, y, z."
    ),
}

# -- Topology section documentation ------------------------------------------

_TOPOLOGY_DOCS: dict[str, str] = {
    "defaults": "Default force-field parameters (nbfunc, comb-rule, gen-pairs, fudgeLJ, fudgeQQ).",
    "atomtypes": "Atom type definitions (name, bonding type, atomic number, mass, charge, ptype, sigma, epsilon).",
    "bondtypes": "Bonded interaction types.",
    "angletypes": "Angle interaction types.",
    "dihedraltypes": "Dihedral interaction types.",
    "constrainttypes": "Constraint types.",
    "pairtypes": "Pair interaction types.",
    "nonbond_params": "Non-bonded interaction parameters between atom type pairs.",
    "moleculetype": "Molecule definition header: name and number of exclusions (nrexcl).",
    "atoms": "Atom entries: nr, type, resnr, residue, atom, cgnr, charge, mass.",
    "bonds": "Bonded interactions: i, j [funct [parameters]].",
    "pairs": "Pair interactions (1-4 non-bonded): i, j [funct [parameters]].",
    "pairs_nb": "Non-bonded pair exclusions.",
    "angles": "Angle interactions: i, j, k [funct [parameters]].",
    "dihedrals": "Dihedral interactions: i, j, k, l [funct [parameters]].",
    "exclusions": "Excluded non-bonded interactions: list of atom indices.",
    "constraints": "Constraints: i, j [funct].",
    "settles": "SETTLE algorithm entries for water (i, funct, dOH, dHH).",
    "virtual_sites2": "Virtual sites from 2 constructing atoms.",
    "virtual_sites3": "Virtual sites from 3 constructing atoms.",
    "virtual_sites4": "Virtual sites from 4 constructing atoms.",
    "virtual_sitesn": "Virtual sites from N constructing atoms.",
    "position_restraints": "Position restraints: ai, funct, fc(x), fc(y), fc(z).",
    "distance_restraints": "Distance restraints: i, j, type, index, type, low, up1, up2, fac.",
    "dihedral_restraints": "Dihedral restraints: ai, aj, ak, al, type, phi, dphi, fc.",
    "orientation_restraints": "Orientation restraints.",
    "angle_restraints": "Angle restraints: ai, aj, ak, al, type, theta, fc.",
    "angle_restraints_z": "Angle restraints along z-axis.",
    "system": "System name (free-text).",
    "molecules": "Molecule list: name and count.",
}

# -- MDP value validation ----------------------------------------------------

_MDP_VALID_VALUES: dict[str, set[str]] = {
    "integrator": {
        "md", "steep", "cg", "l-bfgs", "md-vv", "md-vv-avek",
        "nm", "tpi", "tpic", "mimic", "bending",
        "umbrella-integration",
    },
    "cutoff-scheme": {"verlet", "group"},
    "coulombtype": {
        "PME", "PME-Switch", "PME-User", "Ewald",
        "Reaction-Field", "Cut-off", "Shift", "User", "Generic", "Reply",
    },
    "constraints": {"none", "all-bonds", "h-bonds", "all-angles"},
    "constraint-algorithm": {"lincs", "shake"},
    "tcoupl": {"no", "berendsen", "nose-hoover", "andersen", "v-rescale"},
    "pcoupl": {"no", "berendsen", "parrinello-rahman", "mttk", "c-rescale"},
    "gen-vel": {"yes", "no"},
    "pbc": {"xyz", "no", "xy", "xz", "yz", "x", "y", "z"},
}


def mdp_hover(key: str) -> Optional[str]:
    """Return hover documentation for *key* (case-insensitive).

    Returns ``None`` when the key is unknown.
    """
    return _MDP_DOCS.get(key.lower())


def topology_hover(section_name: str) -> Optional[str]:
    """Return hover documentation for a topology section (case-insensitive).

    Returns ``None`` when the section is unknown.
    """
    return _TOPOLOGY_DOCS.get(section_name.lower())


def get_valid_mdp_values(key: str) -> Optional[set[str]]:
    """Return the set of valid values for a validated MDP key, or None."""
    return _MDP_VALID_VALUES.get(key.lower())
