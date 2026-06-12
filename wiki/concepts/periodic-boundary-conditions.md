# 周期性边界条件 / Periodic Boundary Conditions (PBC)

## 概述 / Overview

周期性边界条件 (PBC) 是分子动力学模拟中用于模拟体相系统（无限系统）的技术。

## 基本原理 / Basic Principle

```
模拟盒子在所有方向上无限重复：
┌───┬───┬───┐
│ A │ A │ A │
├───┼───┼───┤
│ A │ A │ A │  A = 原始盒子
├───┼───┼───┤
│ A │ A │ A │
└───┴───┴───┘
```

当原子离开盒子一侧时，它会从对侧重新进入。

## 盒子类型 / Box Types

### 立方盒子 / Cubic Box

```bash
gmx editconf -f protein.gro -o boxed.gro -bt cubic -d 1.0
```

- 适合：球形蛋白质
- 效率：高

### 十二面体盒子 / Dodecahedral Box

```bash
gmx editconf -f protein.gro -o boxed.gro -bt dodecahedron -d 1.0
```

- 适合：球形蛋白质
- 效率：比立方高 12%
- 体积：约为立方盒子的 0.71 倍

### 八面体盒子 / Octahedral Box

```bash
gmx editconf -f protein.gro -o boxed.gro -bt octahedron -d 1.0
```

- 适合：球形蛋白质
- 效率：与十二面体类似
- 体积：约为立方盒子的 0.71 倍

### 三斜盒子 / Triclinic Box

```bash
gmx editconf -f protein.gro -o boxed.gro -bt triclinic
```

- 适合：膜系统、各向异性系统
- 需要定义全部 9 个盒子向量

## MDP 设置 / MDP Settings

```mdp
pbc = xyz               ; 在所有方向应用 PBC
; 或 xy, xz, yz, x, y, z, no
```

### PBC 选项

| 选项 | 描述 |
|------|------|
| `xyz` | 三维周期性 (最常用) |
| `xy` | 仅 XY 方向周期性 |
| `no` | 无周期性 (真空模拟) |

## 最小镜像约定 / Minimum Image Convention

计算两原子间距离时，使用最短镜像距离：

```
r = min(|r|, |r - L|, |r + L|)
```

其中 L 是盒子长度。

## 处理 PBC / Handling PBC

### 轨迹处理 / Trajectory Processing

```bash
# 跳回主盒子
gmx trjconv -pbc nojump -s topol.tpr -f traj.xtc -o processed.xtc

# 使分子完整
gmx trjconv -pbc mol -s topol.tpr -f traj.xtc -o whole.xtc

# 重新居中
gmx trjconv -pbc mol -center -s topol.tpr -f traj.xtc -o centered.xtc
```

### 距离计算 / Distance Calculation

使用 `-pbc` 选项确保正确计算：

```bash
gmx distance -s topol.tpr -f traj.xtc -n index.ndx \
    -select 'group "Protein" plus group "Ligand"' \
    -pbc yes
```

## 截断与 PBC / Cutoffs and PBC

```mdp
; 截断距离必须小于盒子的一半
rvdw = 1.0               ; VdW 截断
rcoulomb = 1.0           ; 库仑截断
; 盒子边长必须 > 2.0 nm
```

## 真空模拟 / Vacuum Simulation

```mdp
pbc = no
```

适用于：
- 小分子气相模拟
- 簇合物计算
- 质谱分析模拟

## 常见问题 / Common Issues

### 1. 原子穿越边界 / Atoms Crossing Boundaries

**症状**: 原子出现在盒子边缘

**解决**: 使用 `trjconv -pbc nojump`

### 2. 分子断裂 / Molecules Breaking Across Boundaries

**症状**: 分子的一部分在边界一侧，另一部分在另一侧

**解决**: 使用 `trjconv -pbc mol`

### 3. 截断过大 / Cutoff Too Large

**症状**: 能量不守恒，模拟崩溃

**解决**: 减小截断距离或增大盒子

## 参考资料 / References

- GROMACS PBC: https://manual.gromacs.org/current/reference-manual/algorithms/periodic-boundary-conditions.html
