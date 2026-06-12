# GROMACS Free Energy Calculations

> Source: https://manual.gromacs.org/current/reference-manual/algorithms/free-energy-calculations.html
> Tutorial: http://www.mdtutorials.com/gmx/2018/free_energy/01_theory.html
> Captured: 2026-06-12

## Theory

Free energy differences calculated via thermodynamic cycles. The coupling parameter lambda interpolates between state A (lambda=0) and state B (lambda=1):

```
H(p,q;0) = H^A(p,q)
H(p,q;1) = H^B(p,q)
```

### Helmholtz Free Energy

```
dA/dlambda = <dH/dlambda>_{NVT;lambda}

A^B - A^A = integral_0^1 <dH/dlambda> dlambda
```

### Gibbs Free Energy

```
G^B - G^A = integral_0^1 <dH/dlambda>_{NpT;lambda} dlambda
```

## Methods

### 1. Slow Growth

Hamiltonian changes slowly from A to B in a single simulation. Check reversibility by running A->B and B->A.

### 2. Thermodynamic Integration (TI)

Evaluate `<dG/dlambda>` at multiple fixed lambda values:

```mdp
free-energy = yes
init-lambda-state = 0    ; or 1, 2, ..., N
delta-lambda = 0          ; fixed lambda
```

Integrate numerically after collecting all lambda windows.

### 3. Bennett Acceptance Ratio (BAR)

```
gmx bar -f dhdl.xvg
```

Uses energy differences between neighboring lambda states. Requires `calc-lambda-neighbors = 1`.

### 4. MBAR

Multistate BAR, requires all lambda energies:
```mdp
calc-lambda-neighbors = -1
```
Analyzed with external `pymbar` package.

## MDP Configuration

```mdp
free-energy = yes
init-lambda-state = 0

; Lambda vectors
coul-lambdas = 0.0 0.25 0.5 0.75 1.0
vdw-lambdas  = 0.0 0.0  0.0 0.0  0.0

; Soft-core parameters
sc-function = beutler
sc-alpha = 0.5
sc-power = 1
sc-sigma = 0.3

; Output
nstdhdl = 100
separate-dhdl-file = yes
calc-lambda-neighbors = 1
```

## Lambda Components

| Component | Controls |
|-----------|----------|
| `coul-lambdas` | Electrostatic interactions |
| `vdw-lambdas` | Van der Waals interactions |
| `bonded-lambdas` | Bonded interactions |
| `restraint-lambdas` | Restraint interactions |
| `mass-lambdas` | Particle masses |
| `temperature-lambdas` | Temperatures (simulated tempering) |
| `fep-lambdas` | All unspecified components |

## Soft-Core Potentials

Prevent singularities when atoms appear/disappear:

### Beutler et al.
```mdp
sc-function = beutler
sc-alpha = 0.5        ; soft-core parameter
sc-r-power = 6        ; radial power
sc-power = 1          ; lambda power
sc-sigma = 0.3        ; nm, minimum sigma
sc-coul = no          ; apply to Coulomb too?
```

### Gapsys et al.
```mdp
sc-function = gapsys
sc-gapsys-scale-linpoint-lj = 0.85
sc-gapsys-scale-linpoint-q = 0.3
sc-gapsys-sigma-lj = 0.3
```

## Alchemical Transformations

### Decoupling a molecule
```mdp
couple-moltype = Ligand
couple-lambda0 = vdw-q    ; all interactions on
couple-lambda1 = none      ; all interactions off
couple-intramol = no       ; proper vacuum reference
```

### Lambda schedule best practice
1. First turn off Coulomb (coul-lambdas 0->1)
2. Then turn off VdW (vdw-lambdas 0->1)
3. Use soft-core for VdW to avoid singularities

## Analysis

```bash
# BAR analysis
gmx bar -f dhdl.xvg -o bar.xvg

# TI analysis
gmx energy -f ener.edr -o dHdl.xvg

# Combine TI windows
# Use numerical integration (trapezoid, Simpson)
```

## Common Workflows

1. **Solvation free energy**: Decouple molecule in water (complex) and vacuum (simple)
2. **Binding free energy**: Decouple ligand in protein complex and in water
3. **Mutation free energy**: Change residue type A -> B
