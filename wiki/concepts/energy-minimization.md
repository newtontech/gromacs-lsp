# 能量最小化 / Energy Minimization

## 概述 / Overview

能量最小化是分子动力学模拟的第一步，用于消除结构中的不良接触（原子重叠或过于接近）。

## 为什么需要能量最小化？ / Why Energy Minimization?

1. **消除不良接触**: 原子间重叠导致的高能量
2. **稳定结构**: 使系统达到局部最小能量状态
3. **避免模拟崩溃**: 高能量状态可能导致模拟不稳定
4. **准备平衡系统**: 为 NVT/NPT 平衡做准备

## 最小化算法 / Minimization Algorithms

### 1. 最速下降 / Steepest Descent

```mdp
integrator = steep
```

- **优点**: 稳定，处理高梯度好
- **缺点**: 接近最小值时收敛慢
- **适用**: 初步最小化

### 2. 共轭梯度 / Conjugate Gradient

```mdp
integrator = cg
```

- **优点**: 比最速下降收敛快
- **缺点**: 对高梯度不稳定
- **适用**: 精细最小化

### 3. L-BFGS

```mdp
integrator = l-bfgs
```

- **优点**: 快速收敛，内存效率高
- **缺点**: 需要存储历史
- **适用**: 大系统

## 典型 MDP 设置 / Typical MDP Settings

### 基本设置 / Basic Settings

```mdp
; 最小化控制
integrator = steep           ; 或 cg, l-bfgs
emtol = 1000                ; 收敛容差 (kJ/mol/nm)
emstep = 0.01               ; 初始步长 (nm)
nsteps = 50000              ; 最大步数

; 没有温度和压力耦合
tcoupl = no
pcoupl = no

; 截断
cutoff-scheme = Verlet
rcoulomb = 1.0
rvdw = 1.0

; 约束
constraints = none          ; 最小化时通常不约束
```

### 进阶设置 / Advanced Settings

```mdp
integrator = steep
emtol = 100                 ; 更严格
emstep = 0.005              ; 更小步长
nsteps = 100000             ; 更多步数

; 使用约束以加速
constraints = h-bonds
constraint-algorithm = LINCS
```

## 收敛标准 / Convergence Criteria

### emtol 参数 / emtol Parameter

```mdp
emtol = 1000               ; kJ/mol/nm
```

- `1000`: 粗略最小化（快速）
- `100`: 中等最小化
- `10`: 精细最小化（慢）

### 监控收敛 / Monitoring Convergence

```bash
# 运行最小化
gmx grompp -f minim.mdp -c struct.gro -p topol.top -o min.tpr
gmx mdrun -deffnm min

# 检查能量
gmx energy -f min.edr -o potential.xvg
# 选择 Potential
```

## 最小化策略 / Minimization Strategies

### 策略 1: 粗略 + 精细 / Rough + Fine

```bash
# 第一步：粗略最小化
gmx grompp -f steep.mdp -c struct.gro -p topol.top -o min1.tpr
gmx mdrun -deffnm min1

# 第二步：精细最小化
gmx grompp -f cg.mdp -c min1.gro -p topol.top -o min2.tpr
gmx mdrun -deffnm min2
```

### 策略 2: 约束最小化 / Constrained Minimization

```mdp
; 约束重原子以加速
constraints = all-bonds
freezegrps = Protein
```

### 策略 3: 位置限制最小化 / Position-Restrained Minimization

```mdp
; 使用位置限制
define = -DPOSRES
```

## 常见问题 / Common Issues

### 1. 不收敛 / Not Converging

**症状**: 达到最大步数仍不满足 emtol

**解决**:
- 增加 `nsteps`
- 放宽 `emtol`
- 检查结构是否有严重问题

### 2. 能量增加 / Energy Increasing

**症状**: 势能持续上升

**解决**:
- 减小 `emstep`
- 检查力场参数
- 验证拓扑文件

### 3. " LINCS" 警告 / LINCS Warnings

**症状**: LINCS 约束警告

**解决**:
- 减小 `emstep`
- 使用 `constraints = none`

## 验证最小化 / Verifying Minimization

```bash
# 检查最大力
gmx energy -f min.edr
# 选择 "Maximum force"

# 应该 < emtol
```

## 后续步骤 / Next Steps

最小化后：
1. NVT 平衡 (温度耦合)
2. NPT 平衡 (压力耦合)
3. 生产模拟

## 参考资料 / References

- GROMACS 能量最小化: https://manual.gromacs.org/current/reference-manual/algorithms/energy-minimization.html
