# 平衡模拟 / Equilibration

## 概述 / Overview

平衡是分子动力学模拟中的关键步骤，用于将系统从最小化状态过渡到稳定的、具有目标温度和压力的状态。

## 平衡阶段 / Equilibration Stages

### 1. NVT 平衡 / NVT Equilibration

**目标**: 使系统达到目标温度

```mdp
integrator = md
dt = 0.002
nsteps = 50000

; 温度耦合
tcoupl = V-rescale
tc-grps = Protein Water_Non_Water
tau_t = 0.5 0.5
ref_t = 300 300

; 压力耦合关闭
pcoupl = no

; 位置限制（可选）
define = -DPOSRES
```

### 2. NPT 平衡 / NPT Equilibration

**目标**: 使系统达到目标温度和压力

```mdp
integrator = md
dt = 0.002
nsteps = 50000

; 温度耦合
tcoupl = V-rescale
tc-grps = Protein Water_Non_Water
tau_t = 0.5 0.5
ref_t = 300 300

; 压力耦合
pcoupl = Parrinello-Rahman
pcoupltype = isotropic
tau_p = 2.0
ref_p = 1.0
compressibility = 4.5e-5
```

## 温度耦合方法 / Temperature Coupling Methods

### 1. Berendsen 温度耦合

```mdp
tcoupl = Berendsen
tau_t = 0.5          ; 耦合常数 (ps)
```

- **优点**: 快速达到目标温度
- **缺点**: 不产生正确的系综
- **用途**: 初步平衡

### 2. V-rescale (Velocity Rescale)

```mdp
tcoupl = V-rescale
tau_t = 0.5
```

- **优点**: 产生正确的正则系综
- **缺点**: 比 Berendsen 稍慢
- **用途**: 生产模拟

### 3. Nose-Hoover

```mdp
tcoupl = Nose-Hoover
tau_t = 0.5
```

- **优点**: 严格的正则系综
- **缺点**: 可能产生振荡
- **用途**: 精确模拟

## 压力耦合方法 / Pressure Coupling Methods

### 1. Berendsen 压力耦合

```mdp
pcoupl = Berendsen
tau_p = 2.0          ; 耦合常数 (ps)
```

- **优点**: 快速达到目标压力
- **缺点**: 不产生正确的系综
- **用途**: 初步平衡

### 2. Parrinello-Rahman

```mdp
pcoupl = Parrinello-Rahman
tau_p = 2.0
```

- **优点**: 产生正确的等压系综
- **缺点**: 可能不稳定
- **用途**: 生产模拟

## 位置限制策略 / Position Restraint Strategies

### 逐步释放 / Gradual Release

```bash
# 阶段 1: 强限制
define = -DPOSRES -DPOSRES_STRONG
; fc = 1000 kJ/mol/nm²

# 阶段 2: 中等限制
define = -DPOSRES
; fc = 100 kJ/mol/nm²

# 阶段 3: 弱限制
define = -DPOSRES_WEAK
; fc = 10 kJ/mol/nm²

# 阶段 4: 无限制
; 无 define
```

### 选择性限制 / Selective Restraints

```top
#ifdef POSRES_BB
; 仅限制骨架
#include "posre_bb.itp"
#endif
```

## 监控平衡 / Monitoring Equilibration

### 1. 温度监控 / Temperature Monitoring

```bash
gmx energy -f nvt.edr -o temperature.xvg
# 选择 "Temperature"
```

### 2. 压力监控 / Pressure Monitoring

```bash
gmx energy -f npt.edr -o pressure.xvg
# 选择 "Pressure"
```

### 3. 密度监控 / Density Monitoring

```bash
gmx energy -f npt.edr -o density.xvg
# 选择 "Density"
```

### 4. RMSD 监控 / RMSD Monitoring

```bash
gmx rms -s npt.tpr -f npt.xtc -o rmsd.xvg
```

## 收敛标准 / Convergence Criteria

### 温度 / Temperature

- 目标温度 ± 5 K
- 波动稳定在 ± 10 K 内

### 压力 / Pressure

- 目标压力 ± 10 bar
- 无长期漂移

### 密度 / Density

- 蛋白质系统: ~1000 kg/m³
- 膜系统: ~1020 kg/m³
- 趋于稳定值

## 常见问题 / Common Issues

### 1. 温度不收敛 / Temperature Not Converging

**解决**:
- 检查 `tau_t` 设置
- 验证耦合组
- 减小 `dt`

### 2. 压力不稳定 / Pressure Unstable

**解决**:
- 增加 `tau_p`
- 检查盒子尺寸
- 使用 `pcoupl = Berendsen` 开始

### 3. 系统崩溃 / System Crashing

**解决**:
- 使用位置限制
- 减小 `dt`
- 检查初始结构

## 典型工作流 / Typical Workflow

```
能量最小化 → NVT 平衡 (50-100 ps) → NPT 平衡 (100-200 ps) → 生产模拟
```

## 参考资料 / References

- GROMACS 平衡: https://manual.gromacs.org/current/reference-manual/algorithms/thermostats.html
