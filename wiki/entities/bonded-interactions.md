# 键合相互作用 / Bonded Interactions

## 概述 / Overview

键合相互作用描述通过化学键连接的原子之间的相互作用，包括键、角、二面角等。

## 键 / Bonds

### 定义 / Definition

两个原子之间的伸缩振动。

### [bonds] 部分 / [bonds] Section

```top
[ bonds ]
; ai   aj   funct   b0      kb
1     2    1       0.153   334720
```

参数：
- `ai, aj`: 原子索引
- `funct`: 函数类型
- `b0`: 平衡键长 (nm)
- `kb`: 力常数 (kJ/mol/nm²)

### 函数类型 / Function Types

| Type | 描述 | 参数 |
|------|------|------|
| 1 | 简谐势 | b0, kb |
| 2 | FENE (聚合物) | b0, kb |
| 3 | 谐振势 + 第四项 | b0, kb, ... |
| 4 | 限制 | d |
| 5 | 表格势 | - |
| 6 | Morse 势 | b0, D, beta |

### 简谐势函数 / Harmonic Function

```
V = ½kb(r - b0)²
```

## 角 / Angles

### 定义 / Definition

三个连续原子之间的弯曲振动。

### [angles] 部分 / [angles] Section

```top
[ angles ]
; ai   aj   ak   funct   th0     cth
1     2    3    1       109.5   460.24
```

参数：
- `ai, aj, ak`: 原子索引 (中心原子为 aj)
- `funct`: 函数类型
- `th0`: 平衡角度 (度)
- `cth`: 力常数 (kJ/mol/rad²)

### 函数类型 / Function Types

| Type | 描述 | 参数 |
|------|------|------|
| 1 | 简谐势 | th0, cth |
| 2 | 限制 | th0 |
| 3 | Urey-Bradley | th0, cth, r13, k13 |
| 4 | 四角余弦 | th0, cth, ... |
| 5 | 表格势 | - |

## 二面角 / Dihedrals

### 定义 / Definition

四个连续原子之间的扭转势能。

### [dihedrals] 部分 / [dihedrals] Section

```top
[ dihedrals ]
; ai   aj   ak   al   funct   phi0    fc
1     2    3    4    9       0.0     15.7
```

参数：
- `ai, aj, ak, al`: 原子索引
- `funct`: 函数类型
- `phi0`: 相位角 (度)
- `fc`: 力常数 (kJ/mol)

### 函数类型 / Function Types

| Type | 描述 | 参数 |
|------|------|------|
| 1 | 简谐势 | phi0, fc |
| 2 | 禁止二面角 | - |
| 3 | Ryckaert-Bellemans | C0, C1, C2, C3, C4, C5 |
| 4 | 正弦级数 | phi0, fc, mult |
| 8 | 四角余弦 | C0, C1, C2, C3, C4, C5 |
| 9 | 正弦级数 (charmm) | phi0, fc, mult |

### Ryckaert-Bellemans 函数

```
V = C0 + C1*cos(φ) + C2*cos²(φ) + C3*cos³(φ) + C4*cos⁴(φ) + C5*cos⁵(φ)
```

## 1-4 相互作用 / 1-4 Interactions

### [pairs] 部分 / [pairs] Section

```top
[ pairs ]
; ai   aj   funct   fudge   fudgeQQ
1     5    1       0.5     0.8333
```

处理被两个键分隔的原子间相互作用（通常在二面角中）。

## 约束 / Constraints

### 定义 / Definition

固定原子间的距离，减少高频振动，允许更大的时间步长。

### [constraints] 部分 / [constraints] Section

```top
[ constraints ]
; ai   aj   funct   d
1     2    1       0.1
```

### 常见约束 / Common Constraints

- **氢键约束**: 使用 `constraints = h-bonds`
- **全键约束**: 使用 `constraints = all-bonds`
- **全角度约束**: 使用 `constraints = all-angles`

### 约束算法 / Constraint Algorithms

- **LINCS**: 默认，稳定
- **SHAKE**: 经典算法

## SETTLE / SETTLE Algorithm

用于水分子的刚性约束：

```top
[ settles ]
; i   funct   dOH   dHH
1    1       0.09572  0.15139
```

## 虚拟位点 / Virtual Sites

质量为零的虚拟原子，位置由构造原子计算得出。

### [virtual_sites2] 部分 / [virtual_sites2 Section]

```top
[ virtual_sites2 ]
; i   f1  f2   funct
1    2   3    1
```

## 参考资料 / References

- GROMACS 键合相互作用: https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html
