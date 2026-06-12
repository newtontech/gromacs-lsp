# GROMACS MDP Complete Parameter Reference

> Source: https://manual.gromacs.org/current/user-guide/mdp-options.html
> GROMACS version: 2026.2 (current)
> Captured: 2026-06-12

This is the complete reference for all MDP (Molecular Dynamics Parameters) options in GROMACS.

## Preprocessing

- `include` — directories to include in topology. Format: `-I/home/john/mylib -I../otherlib`
- `define` — defines to pass to preprocessor. Examples: `-DFLEXIBLE`, `-DPOSRES`

## Run Control

- `integrator` — Algorithm selection:
  - `md` — leap-frog integrator
  - `md-vv` — velocity Verlet
  - `md-vv-avek` — velocity Verlet with averaged kinetic energy
  - `sd` — stochastic dynamics
  - `bd` — Brownian dynamics
  - `steep` — steepest descent minimization
  - `cg` — conjugate gradient minimization
  - `l-bfgs` — quasi-Newton L-BFGS minimization
  - `nm` — normal mode analysis
  - `tpi` — test particle insertion
  - `tpic` — test particle insertion in cavity
  - `mimic` — MiMiC QM/MM coupling
- `tinit` (0) [ps] — starting time
- `dt` (0.001) [ps] — time step
- `nsteps` (0) — maximum number of steps, -1 for no maximum
- `init-step` (0) — starting step number
- `simulation-part` (0) — simulation part number
- `mts` — multiple time-stepping (yes/no)
- `mts-levels` (2) — number of MTS levels
- `mts-level2-forces` — force groups for level 2: longrange-nonbonded, nonbonded, pair, dihedral, angle, pull, awh
- `mts-level2-factor` (2) — interval for level 2 forces
- `mass-repartition-factor` (1) — mass scaling for light atoms (3 enables 4fs timestep with h-bond constraints)
- `comm-mode` — COM motion removal: Linear, Angular, Linear-acceleration-correction, None
- `nstcomm` (100) [steps] — interval for COM motion removal
- `comm-grps` — groups for COM motion removal

## Langevin Dynamics

- `bd-fric` (0) [amu ps-1] — Brownian dynamics friction coefficient
- `ld-seed` (-1) — random seed for stochastic/Brownian dynamics

## Energy Minimization

- `emtol` (10.0) [kJ mol-1 nm-1] — convergence tolerance
- `emstep` (0.01) [nm] — initial step size
- `nstcgsteep` (1000) — interval for steepest descent in CG
- `nbfgscorr` (10) — correction steps for L-BFGS

## Shell MD

- `niter` (20) — max iterations for shell optimization
- `fcstep` (0) [ps2] — step size for flexible constraint optimization

## Test Particle Insertion

- `rtpi` (0.05) [nm] — TPI radius

## Output Control

- `nstxout` (0) — coordinate output interval to trr
- `nstvout` (0) — velocity output interval to trr
- `nstfout` (0) — force output interval to trr
- `nstlog` (1000) — log output interval
- `nstcalcenergy` (100) — energy calculation interval
- `nstenergy` (1000) — energy file output interval
- `nstxout-compressed` (0) — compressed xtc output interval
- `compressed-x-precision` (1000) — xtc precision
- `compressed-x-grps` — groups for compressed output
- `energygrps` — groups for non-bonded energy output

## Neighbor Searching

- `cutoff-scheme` — Verlet (default) or group (unsupported)
- `nstlist` (10) — neighbor list update interval
- `pbc` — xyz, no, xy
- `periodic-molecules` — no/yes
- `verlet-buffer-tolerance` (0.005) [kJ mol-1 ps-1]
- `verlet-buffer-pressure-tolerance` (0.5) [bar]
- `rlist` (1) [nm] — neighbor list cutoff

## Electrostatics

- `coulombtype` — Cut-off, Ewald, PME, P3M-AD, Reaction-Field, User, PME-Switch, PME-User, PME-User-Switch
- `coulomb-modifier` — Potential-shift, None
- `rcoulomb-switch` (0) [nm]
- `rcoulomb` (1) [nm]
- `epsilon-r` (1) — relative dielectric constant
- `epsilon-rf` (0) — reaction field dielectric

## Van der Waals

- `vdwtype` — Cut-off, PME, Shift (deprecated), Switch (deprecated), User
- `vdw-modifier` — Potential-shift, None, Force-switch, Potential-switch
- `rvdw-switch` (0) [nm]
- `rvdw` (1) [nm]
- `DispCorr` — no, EnerPres, Ener

## Ewald / PME

- `fourierspacing` (0.12) [nm]
- `fourier-nx/ny/nz` (0) — override grid dimensions
- `pme-order` (4) — interpolation order (3-12)
- `ewald-rtol` (10-5) — electrostatic tolerance
- `ewald-rtol-lj` (10-3) — LJ-PME tolerance
- `lj-pme-comb-rule` — Geometric, Lorentz-Berthelot
- `ewald-geometry` — 3d, 3dc
- `epsilon-surface` (0)

## Temperature Coupling

- `ensemble-temperature-setting` — auto, constant, variable, not-available
- `ensemble-temperature` (-1) [K]
- `tcoupl` — no, berendsen, nose-hoover, andersen, andersen-massive, v-rescale
- `nsttcouple` (-1)
- `nh-chain-length` (10)
- `tc-grps` — coupling groups
- `tau-t` [ps] — coupling time constant
- `ref-t` [K] — reference temperature

## Pressure Coupling

- `pcoupl` — no, Berendsen, C-rescale, Parrinello-Rahman, MTTK
- `pcoupltype` — isotropic, semiisotropic, anisotropic, surface-tension
- `nstpcouple` (-1)
- `tau-p` (5) [ps]
- `compressibility` [bar-1]
- `ref-p` [bar]
- `refcoord-scaling` — no, all, com

## Simulated Annealing

- `annealing` — no, single, periodic
- `annealing-npoints`
- `annealing-time`
- `annealing-temp`

## Velocity Generation

- `gen-vel` — no, yes
- `gen-temp` (300) [K]
- `gen-seed` (-1)

## Bonds / Constraints

- `constraints` — none, h-bonds, all-bonds, h-angles (deprecated), all-angles (deprecated)
- `constraint-algorithm` — LINCS, SHAKE
- `continuation` — no, yes
- `shake-tol` (0.0001)
- `lincs-order` (4)
- `lincs-iter` (1)
- `lincs-warnangle` (30) [deg]
- `morse` — no, yes

## Walls

- `nwall` (0) — 0, 1, or 2
- `wall-atomtype`
- `wall-type` — 9-3, 10-4, 12-6, table
- `wall-r-linpot` (-1) [nm]
- `wall-density` [nm-3/nm-2]
- `wall-ewald-zfac` (3)

## COM Pulling

- `pull` — no, yes
- `pull-cylinder-r` (1.5) [nm]
- `pull-constr-tol` (10-6)
- `pull-print-com` — no, yes
- `pull-print-ref-value` — no, yes
- `pull-print-components` — no, yes
- `pull-nstxout` (50)
- `pull-nstfout` (50)
- `pull-ngroups` (1)
- `pull-ncoords` (1)
- `pull-group1-name`, `pull-group1-weights`, `pull-group1-pbcatom`
- `pull-coord1-type` — umbrella, constraint, constant-force, flat-bottom, flat-bottom-high, external-potential
- `pull-coord1-geometry` — distance, direction, direction-periodic, direction-relative, cylinder, angle, angle-axis, dihedral, transformation
- `pull-coord1-expression` — math expression for transformation
- `pull-coord1-groups`, `pull-coord1-dim`, `pull-coord1-origin`, `pull-coord1-vec`
- `pull-coord1-start`, `pull-coord1-init`, `pull-coord1-rate`, `pull-coord1-k`, `pull-coord1-kB`

## AWH Adaptive Biasing

- `awh` — no, yes
- `awh-potential` — convolved, umbrella
- `awh-seed` (-1)
- `awh-nstout` (100000), `awh-nstsample` (10), `awh-nsamples-update` (100)
- `awh-nbias` (1)
- `awh1-error-init` (10.0) [kJ mol-1]
- `awh1-growth` — exp-linear, linear
- `awh1-target` — constant, cutoff, boltzmann, local-boltzmann
- `awh1-ndim` (1)
- `awh1-dim1-coord-provider` — pull, fep-lambda
- `awh1-dim1-force-constant`, `awh1-dim1-start`, `awh1-dim1-end`, `awh1-dim1-diffusion`

## Enforced Rotation

- `rotation` — no, yes
- `rot-ngroups` (1)
- `rot-group0`, `rot-type0`, `rot-vec0`, `rot-pivot0`, `rot-rate0`, `rot-k0`

## NMR Refinement

- `disre` — no, simple, ensemble
- `disre-weighting` — equal, conservative
- `disre-fc` (1000) [kJ mol-1 nm-2]
- `orire` — no, yes

## Free Energy Calculations

- `free-energy` — no, yes, expanded
- `init-lambda` (-1), `delta-lambda` (0), `init-lambda-state` (-1)
- `fep-lambdas`, `coul-lambdas`, `vdw-lambdas`, `bonded-lambdas`, `restraint-lambdas`, `mass-lambdas`, `temperature-lambdas`
- `calc-lambda-neighbors` (1)
- `sc-function` — beutler, gapsys
- `sc-alpha` (0), `sc-r-power` (6), `sc-coul` (no), `sc-power` (1), `sc-sigma` (0.3)
- `couple-moltype`, `couple-lambda0` (vdw-q), `couple-lambda1` (vdw-q)
- `couple-intramol` — no, yes
- `nstdhdl` (100), `dhdl-derivatives` (yes)

## Expanded Ensemble

- `nstexpanded`, `lmc-stats`, `lmc-mc-move`, `lmc-seed`
- `simulated-tempering` (no), `sim-temp-low` (300), `sim-temp-high` (300)

## Non-equilibrium MD

- `acc-grps`, `accelerate`, `freezegrps`, `freezedim`
- `cos-acceleration` (0), `deform` (0 0 0 0 0 0)

## Electric Fields

- `electric-field-x/y/z` — E0 omega t0 sigma

## QM/MM

- `qmmm-cp2k-active` (false)
- `qmmm-cp2k-qmgroup`, `qmmm-cp2k-qmmethod`, `qmmm-cp2k-qmcharge`, `qmmm-cp2k-qmmultiplicity`

## Computational Electrophysiology

- `swapcoords` — no, X, Y, Z
- `swap-frequency` (1), `split-group0`, `split-group1`, `solvent-group`

## Density-guided Simulations

- `density-guided-simulation-active` (no)
- `density-guided-simulation-group` (protein)
- `density-guided-simulation-similarity-measure` — inner-product, relative-entropy, cross-correlation

## Colvars Module

- `colvars-active` (false)
- `colvars-configfile`, `colvars-seed` (-1)

## NNP/MM (Neural Network Potentials)

- `nnpot-active` (false)
- `nnpot-modelfile`, `nnpot-input-group`, `nnpot-embedding` (mechanical/electrostatic-model)

## FMM Interface

- `fmm-backend` — inactive, exafmm, fmsolvr
