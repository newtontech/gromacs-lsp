# Pull 代码 / Pull Code

## 概述 / Overview

Pull 代码用于对原子或原子组施加力，常用于伞状采样 (umbrella sampling)、强制展开、结合自由能计算等。

## 基本概念 / Basic Concepts

Pull 代码通过施加外部力或约束来实现：

1. **伞状采样**: 沿反应坐标施加约束力
2. **恒力拉动**: 施加恒定力
3. **强制变形**: 改变几何参数

## MDP 设置 / MDP Settings

### 启用 Pull 代码 / Enable Pull Code

```mdp
pull = yes
pull-ngroups = 2           ; 组数
pull-ncoords = 1           ; 坐标数
```

### 定义 Pull 组 / Define Pull Groups

```mdp
pull-group1-name = Protein
pull-group1-type = simple
pull-group1-index-grps = Protein
pull-group1-pbcatom = 1    ; 参考原子

pull-group2-name = Ligand
pull-group2-type = simple
pull-group2-index-grps = Ligand
pull-group2-pbcatom = 1
```

### 定义 Pull 坐标 / Define Pull Coordinates

```mdp
pull-coord1-type = umbrella     ; 或 constraint, constant-force
pull-coord1-geometry = distance ; 或 direction, position
pull-coord1-groups = 1 2
pull-coord1-dim = Y Y Y         ; 沿哪些轴
pull-coord1-k = 1000           ; 力常数 (kJ/mol/nm²)
pull-coord1-rate = 0.01        ; 速度 (nm/ps)
```

## Pull 类型 / Pull Types

### 1. Umbrella (伞状约束) / Umbrella

```mdp
pull-coord1-type = umbrella
pull-coord1-k = 1000           ; 约束力常数
```

施加简谐势：
```
V = ½k(z - z0)²
```

### 2. Constraint (硬约束) / Constraint

```mdp
pull-coord1-type = constraint
```

使用 LINCS 约束距离。

### 3. Constant-force (恒力) / Constant Force

```mdp
pull-coord1-type = constant-force
pull-coord1-k = 1000           ; 力的大小 (kJ/mol/nm)
```

施加恒定力：
```
F = k
```

## 几何类型 / Geometry Types

### Distance (距离) / Distance

```mdp
pull-coord1-geometry = distance
```

两组间的距离。

### Direction (方向) / Direction

```mdp
pull-coord1-geometry = direction
pull-coord1-vec = 0.0 1.0 0.0   ; 方向向量
```

沿特定方向的距离。

### Position (位置) / Position

```mdp
pull-coord1-geometry = position
pull-coord1-origin = 0.0 0.0 0.0
pull-coord1-dim = Y Y Y
```

到固定点的距离。

## 典型应用 / Typical Applications

### 1. 伞状采样 / Umbrella Sampling

```mdp
pull = yes
pull-ngroups = 2
pull-ncoords = 1

pull-group1-name = Protein
pull-group1-type = simple
pull-group1-index-grps = Protein

pull-group2-name = Ligand
pull-group2-type = simple
pull-group2-index-grps = Ligand

pull-coord1-type = umbrella
pull-coord1-geometry = distance
pull-coord1-groups = 1 2
pull-coord1-k = 1000
```

### 2. SMD (Steered Molecular Dynamics)

```mdp
pull-coord1-type = umbrella
pull-coord1-k = 1000
pull-coord1-rate = 0.01        ; 移动速度
```

### 3. 恒力展开 / Constant Force Unfolding

```mdp
pull-coord1-type = constant-force
pull-coord1-k = 500            ; 500 kJ/mol/nm ≈ 830 pN
```

## 输出 / Output

### Pull 坐标输出 / Pull Coordinate Output

```mdp
pull-coord1-rate = 0.01
nstxout-compressed = 1000
pull-print-compatibility = no
```

### Pull 力输出 / Pull Force Output

```bash
gmx energy -f pull.edr
# 选择 Pull-force
```

## 分析 / Analysis

### 提取 Pull 数据 / Extract Pull Data

```bash
gmx pull -f md.xtc -s md.tpr -o pull.xvg \
    -pullx pullx.xvg -pullf pullf.xvg
```

### WHAM 分析 / WHAM Analysis

```bash
gmx wham -it tpr-files.dat -if pullf-files.dat \
    -o profile.xvg -hist histogram.xvg
```

## 性能考虑 / Performance Considerations

```mdp
; 优化 Pull 性能
pull-coord1-pbc-ref-prev-step = yes
```

## 参考资料 / References

- GROMACS Pull 代码: https://manual.gromacs.org/current/reference-manual/algorithms/pull.html
