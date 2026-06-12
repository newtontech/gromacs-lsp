# 典型工作流 / Typical Workflow

## 概述 / Overview

这是使用 GROMACS 进行分子动力学模拟的完整工作流程，从结构准备到分析。

## 阶段 1: 结构准备 / Structure Preparation

### 1.1 获取结构 / Obtain Structure

```bash
# 从 PDB 数据库
wget https://files.rcsb.org/download/1AKI.pdb

# 或从建模软件导出
```

### 1.2 处理结构 / Process Structure

```bash
# 使用 pdb2gmx 生成拓扑
gmx pdb2gmx -f 1AKI.pdb -o processed.gro \
    -p topol.top -water tip3p -ff amber99sb-ildn
```

**输出**:
- `processed.gro` - 处理后的坐标
- `topol.top` - 拓扑文件
- `posre.itp` - 位置限制文件

### 1.3 定义盒子 / Define Box

```bash
# 添加立方盒子
gmx editconf -f processed.gro -o boxed.gro \
    -c -d 1.0 -bt cubic
```

### 1.4 添加溶剂 / Add Solvent

```bash
# 添加水
gmx solvate -cp boxed.gro -cs spc216.gro -o solvated.gro -p topol.top
```

### 1.5 添加离子 / Add Ions

```bash
# 创建 .tpr 文件
gmx grompp -f ions.mdp -c solvated.gro -p topol.top -o ions.tpr

# 添加离子中和并加盐
gmx genion -s ions.tpr -p topol.top -o solv_ions.gro \
    -pname NA -nname CL -neutral -conc 0.15
```

## 阶段 2: 能量最小化 / Energy Minimization

### 2.1 创建 MDP 文件 / Create MDP File

```mdp
; minim.mdp
integrator = steep
emtol = 1000
emstep = 0.01
nsteps = 50000

cutoff-scheme = Verlet
rcoulomb = 1.0
rvdw = 1.0

constraints = none
```

### 2.2 运行最小化 / Run Minimization

```bash
gmx grompp -f minim.mdp -c solv_ions.gro \
    -p topol.top -o min.tpr

gmx mdrun -deffnm min -v
```

### 2.3 检查收敛 / Check Convergence

```bash
gmx energy -f min.edr -o potential.xvg
# 选择 Potential

gmx energy -f min.edr -o maxforce.xvg
# 选择 Maximum force
```

## 阶段 3: NVT 平衡 / NVT Equilibration

### 3.1 创建 NVT MDP / Create NVT MDP

```mdp
; nvt.mdp
integrator = md
dt = 0.002
nsteps = 50000

tcoupl = V-rescale
tc-grps = Protein Water_and_ions
tau_t = 0.5 0.5
ref_t = 300 300

pcoupl = no

define = -DPOSRES

cutoff-scheme = Verlet
rcoulomb = 1.0
rvdw = 1.0

constraints = h-bonds
```

### 3.2 运行 NVT / Run NVT

```bash
gmx grompp -f nvt.mdp -c min.gro -p topol.top \
    -o nvt.tpr -r min.gro

gmx mdrun -deffnm nvt
```

### 3.3 检查温度 / Check Temperature

```bash
gmx energy -f nvt.edr -o temperature.xvg
# 选择 Temperature
```

## 阶段 4: NPT 平衡 / NPT Equilibration

### 4.1 创建 NPT MDP / Create NPT MDP

```mdp
; npt.mdp
integrator = md
dt = 0.002
nsteps = 50000

tcoupl = V-rescale
tc-grps = Protein Water_and_ions
tau_t = 0.5 0.5
ref_t = 300 300

pcoupl = Parrinello-Rahman
pcoupltype = isotropic
tau_p = 2.0
ref_p = 1.0
compressibility = 4.5e-5

define = -DPOSRES

cutoff-scheme = Verlet
rcoulomb = 1.0
rvdw = 1.0

constraints = h-bonds
```

### 4.2 运行 NPT / Run NPT

```bash
gmx grompp -f npt.mdp -c nvt.gro -p topol.top \
    -o npt.tpr -r nvt.gro -t nvt.cpt

gmx mdrun -deffnm npt
```

### 4.3 检查密度 / Check Density

```bash
gmx energy -f npt.edr -o density.xvg
# 选择 Density
```

## 阶段 5: 生产模拟 / Production Simulation

### 5.1 创建生产 MDP / Create Production MDP

```mdp
; md.mdp
integrator = md
dt = 0.002
nsteps = 50000000

nstxout-compressed = 5000
nstvout = 0
nstenergy = 1000
nstlog = 1000

tcoupl = V-rescale
tc-grps = Protein Water_and_ions
tau_t = 0.5 0.5
ref_t = 300 300

pcoupl = Parrinello-Rahman
tau_p = 2.0
ref_p = 1.0

cutoff-scheme = Verlet
ns_type = grid
nstlist = 10
rlist = 1.0

constraints = h-bonds
```

### 5.2 运行生产模拟 / Run Production

```bash
gmx grompp -f md.mdp -c npt.gro -p topol.top \
    -o md.tpr -t npt.cpt

gmx mdrun -deffnm md
```

## 阶段 6: 分析 / Analysis

### 6.1 处理轨迹 / Process Trajectory

```bash
# 去除周期性
gmx trjconv -s md.tpr -f md.xtc -o nojump.xtc \
    -pbc nojump

# 使分子完整
gmx trjconv -s md.tpr -f nojump.xtc -o whole.xtc \
    -pbc mol

# 居中
gmx trjconv -s md.tpr -f whole.xtc -o centered.xtc \
    -pbc mol -center
```

### 6.2 RMSD 分析 / RMSD Analysis

```bash
gmx rms -s md.tpr -f centered.xtc -o rmsd.xvg
```

### 6.3 RMSF 分析 / RMSF Analysis

```bash
gmx rmsf -s md.tpr -f centered.xtc -o rmsf.xvg
```

### 6.4 氢键分析 / Hydrogen Bond Analysis

```bash
gmx hbond -s md.tpr -f centered.xtc -num hb.xvg
```

## 参考资料 / References

- GROMACS 教程: https://manual.gromacs.org/current/user-guide/
- Justin's 教程: http://www.mdtutorials.com/
