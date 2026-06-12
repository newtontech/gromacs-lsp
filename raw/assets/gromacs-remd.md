# GROMACS Replica Exchange Molecular Dynamics (REMD)

> Source: https://manual.gromacs.org/2026.2/reference-manual/algorithms/replica-exchange.html
> Captured: 2026-06-12

## Overview

Replica exchange molecular dynamics (REMD) speeds up sampling by simulating multiple replicas at different temperatures and exchanging complete states at regular intervals.

## Exchange Probability

The exchange probability between replicas 1 and 2:

```
P(1 <-> 2) = min(1, exp[(1/kB*T1 - 1/kB*T2)(U1 - U2)])
```

After exchange, velocities are scaled by (T1/T2)^{+/-0.5} and a neighbor search is performed.

## Exchange Strategy

In GROMACS, exchanges are attempted for:
- Odd pairs on odd attempts
- Even pairs on even attempts

Example with 4 replicas (0,1,2,3):
- Steps 1000, 3000: pairs 0-1 and 2-3
- Steps 2000, 4000: pair 1-2

## Temperature Selection

The energy difference: `U1 - U2 = N_df * (c/2) * kB * (T1 - T2)`

Where:
- `N_df` = total degrees of freedom (~2*N_atoms with all bonds constrained)
- `c` = 1 for harmonic, ~2 for protein/water systems

For exchange probability of ~0.135: `epsilon ~ 1/sqrt(N_atoms)`

REMD temperature calculator: https://virtualchemistry.org/remd-temperature-generator/

## Isobaric-isothermal Extension (Okabe et al.)

Exchange probability modified to include volume term:

```
P(1 <-> 2) = min(1, exp[(1/kB*T1 - 1/kB*T2)(U1 - U2) +
                         (P1/kB*T1 - P2/kB*T2)(V1 - V2)])
```

## Hamiltonian Replica Exchange

Each replica has a different Hamiltonian defined by free energy pathway:

```
P(1 <-> 2) = min(1, exp[(1/kB*T)(U1(x1) - U1(x2) + U2(x2) - U2(x1))])
```

Hamiltonians defined by lambda values in the mdp file.

## Combined Temperature + Hamiltonian REMD

```
P(1 <-> 2) = min(1, exp[U1(x1) - U1(x2))/(kB*T1) + (U2(x2) - U2(x1))/(kB*T2)])
```

## Gibbs Sampling REMD

All possible pairs tested for exchange (not just neighbors). Requires no additional energy calculations but has extra communication cost.

## MDP Configuration

```mdp
; REMD settings are controlled via mdrun, not mdp
; Run with:
; mdrun -deffn md -multidir sim0 sim1 sim2 ... simN
;   -replex 1000    ; exchange attempt interval (steps)
;   -reseed -1      ; random seed for exchanges
```

## Running REMD

```bash
# Generate N tpr files at different temperatures
gmx grompp -f nvt_300.mdp -o topol_300.tpr
gmx grompp -f nvt_310.mdp -o topol_310.tpr
# ... etc

# Run with MPI
mpirun -np N gmx_mpi mdrun -s topol.tpr \
    -multidir sim0 sim1 sim2 ... simN \
    -replex 1000

# Analyze
gmx energy -f sim*/ener.edr -o temperature.xvg
```

## Requirements

- MPI installation required (inherent parallelism)
- Each replica typically runs on a separate rank
- Temperature spacing must be chosen carefully for adequate exchange rates (~20-25%)
