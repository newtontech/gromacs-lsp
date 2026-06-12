# GROMACS Topology File Formats - Complete Reference

> Source: https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html
> Captured: 2026-06-12

## Topology File Structure

The topology follows a strict hierarchy of three levels:

### Level 1: Parameters

| Directive | Required | Description |
|-----------|----------|-------------|
| `defaults` | mandatory | nbfunc; comb-rule; gen-pairs; fudgeLJ; fudgeQQ |
| `atomtypes` | mandatory | atom type; bonded type; atomic number; mass; charge; ptype; V; W |
| `bondtypes` | optional | bond type parameters |
| `pairtypes` | optional | pair interaction parameters |
| `angletypes` | optional | angle type parameters |
| `dihedraltypes` | optional | dihedral type parameters |
| `constrainttypes` | optional | constraint parameters |
| `nonbond_params` | optional | LJ (func 1) or Buckingham (func 2) |

### Level 2: Molecule Definition

| Directive | Atoms | Func Types | Description |
|-----------|-------|------------|-------------|
| `moleculetype` | - | - | name; nrexcl |
| `atoms` | 1 | - | type; resnr; resname; atomname; cgnr; q; m |
| `bonds` | 2 | 1-10 | Bond interactions |
| `pairs` | 2 | 1-2 | 1-4 interactions |
| `pairs_nb` | 2 | 1 | Extra non-bonded pairs |
| `angles` | 3 | 1-10 | Angle interactions |
| `dihedrals` | 4 | 1-11 | Dihedral interactions |
| `exclusions` | 1 | - | Excluded atom pairs |
| `constraints` | 2 | 1-2 | Constraint distances |
| `settles` | 1 | 1 | SETTLE water constraints |
| `virtual_sites1/2/3/4/n` | varies | varies | Virtual site definitions |
| `position_restraints` | 1 | 1-2 | Position restraints |
| `distance_restraints` | 2 | 1 | Distance restraints |
| `dihedral_restraints` | 4 | 1 | Dihedral restraints |
| `orientation_restraints` | 2 | 1 | Orientation restraints |
| `angle_restraints` | 4 | 1 | Angle restraints |
| `angle_restraints_z` | 2 | 1 | Z-angle restraints |

### Level 3: System

| Directive | Description |
|-----------|-------------|
| `system` | System name |
| `molecules` | molecule_name; count |
| `intermolecular_interactions` | Optional inter-molecular bonded interactions |

## Bond Function Types

| Func | Name | Parameters |
|------|------|-----------|
| 1 | bond | b0 (nm); kb (kJ/mol/nm2) |
| 2 | G96 bond | b0 (nm); kb (kJ/mol/nm4) |
| 3 | Morse | b0 (nm); D (kJ/mol); beta (1/nm) |
| 4 | cubic bond | b0 (nm); C2, C3 |
| 5 | connection | (none) |
| 6 | harmonic | b0 (nm); kb (kJ/mol/nm2) |
| 7 | FENE | bm (nm); kb (kJ/mol/nm2) |
| 8 | tabulated | table number; k |
| 9 | tabulated (no exclusions) | table number; k |
| 10 | restraint potential | low, up1, up2 (nm); kdr |

## Angle Function Types

| Func | Name | Parameters |
|------|------|-----------|
| 1 | angle | theta0 (deg); ktheta (kJ/mol/rad2) |
| 2 | G96 angle | theta0 (deg); ktheta (kJ/mol) |
| 3 | cross bond-bond | r1e, r2e (nm); krr' |
| 4 | cross bond-angle | r1e, r2e, r3e (nm); krtheta |
| 5 | Urey-Bradley | theta0; ktheta; r13 (nm); kUB |
| 6 | quartic angle | theta0; C0-C4 |
| 8 | tabulated angle | table number; k |
| 9 | linear angle | a0; klin |
| 10 | restricted bending | theta0 (deg); ktheta |

## Dihedral Function Types

| Func | Name | Parameters |
|------|------|-----------|
| 1 | proper dihedral | phi_s (deg); kphi (kJ/mol); multiplicity |
| 2 | improper dihedral | xi0 (deg); kxi (kJ/mol/rad2) |
| 3 | Ryckaert-Bellemans | C0-C5 (kJ/mol) |
| 4 | periodic improper | phi_s (deg); kphi; multiplicity |
| 5 | Fourier dihedral | C1-C5 (kJ/mol) |
| 8 | tabulated dihedral | table number; k |
| 9 | proper (multiple) | phi_s; kphi; multiplicity |
| 10 | restricted dihedral | phi0; kphi |
| 11 | combined bending-torsion | kphi; a0-a4 |

## File Format Rules

- Semicolons (`;`) start comments
- Backslash at line end continues to next line
- Directives in `[brackets]`
- Hierarchy must be: parameter -> molecule -> system
- Atoms numbered consecutively starting at 1
- File parsed once (no forward references)
- Multiple bonded interactions of same type allowed on same atoms
- #include and #ifdef/#endif preprocessor directives supported

## Defaults Section

```
[ defaults ]
; nbfunc  comb-rule  gen-pairs  fudgeLJ  fudgeQQ
1         2          yes        0.5      0.8333
```

- `nbfunc`: 1 (LJ) or 2 (Buckingham, unsupported)
- `comb-rule`: 1 (geometric sigma/epsilon), 2 (Lorentz-Berthelot), 3 (geometric sigma)
- `gen-pairs`: yes generates 1-4 params from fudgeLJ
- `fudgeLJ`: factor for LJ 1-4 (default 1)
- `fudgeQQ`: factor for electrostatic 1-4 (default 1)

## Free Energy Topology

Add B-state parameters after A-state on same line:

```
[ atoms ]
; nr type resnr residue atom cgnr charge mass  typeB chargeB massB
  1  H    1     PROP   PH    1     0.398  1.008 CH3   0.0    15.035
```

The lambda-dependence interpolates between A (lambda=0) and B (lambda=1) states.
