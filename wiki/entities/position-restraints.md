# 位置限制 / Position Restraints

## 概述 / Overview

位置限制用于约束特定原子在固定位置附近，常用于：

- 平衡过程中的固定
- 特定区域的限制
- 模拟初始阶段的稳定性

## [position_restraints] 部分 / [position_restraints] Section

```top
[ position_restraints ]
; ai   funct    fc(x)   fc(y)   fc(z)
1     1       1000    1000    1000
2     1       1000       0    1000
3     1       1000       0       0
```

### 参数说明 / Parameters

| 参数 | 描述 |
|------|------|
| `ai` | 原子索引 |
| `funct` | 函数类型 (通常为 1) |
| `fc(x)` | X 方向力常数 (kJ/mol/nm²) |
| `fc(y)` | Y 方向力常数 |
| `fc(z)` | Z 方向力常数 |

### 力常数含义 / Force Constant Meaning

- `1000 1000 1000`: 限制在点 (完全限制)
- `1000 0 1000`: 限制在 Y 轴线 (X 和 Z 限制)
- `1000 0 0`: 限制在 Y-Z 平面 (仅 X 限制)

## 势能函数 / Potential Function

```
V = ½kx(x - x0)² + ½ky(y - y0)² + ½kz(z - z0)²
```

其中 `(x0, y0, z0)` 是参考位置。

## 应用场景 / Use Cases

### 1. 蛋白质骨架固定 / Backbone Restraints

```top
#ifdef POSRES_BB
#include "posre_bb.itp"
#endif
```

### 2. 配体固定 / Ligand Restraints

```top
[ position_restraints ]
; 复杂的配体原子
1    1    1000  1000  1000
2    1    1000  1000  1000
```

### 3. 膜蛋白固定 / Membrane Protein Restraints

固定膜蛋白以允许脂质平衡：

```bash
# 使用 position restraints on protein
# 仅限制 Cα 原子
```

### 4. QMMM 模拟 / QMMM Simulations

```top
[ position_restraints ]
; QM 区域原子
1    1    10000  10000  10000
```

## 生成位置限制文件 / Generating Restraint Files

### 使用 pdb2gmx

```bash
gmx pdb2gmx -f protein.pdb -o processed.gro \
    -p topol.top -i posre.itp -ff amber99sb-ildn \
    -water tip3p
```

生成 `posre.itp` 包含重原子的位置限制。

### 自定义限制 / Custom Restraints

创建自定义 `.itp` 文件：

```top
[ position_restraints ]
; atom  type  fc(x)   fc(y)   fc(z)
; 选择性限制特定原子
5     1    1000    1000    1000
10    1    1000    1000    1000
```

## 力常数选择 / Force Constant Selection

| 场景 | 力常数 | 描述 |
|------|--------|------|
| 强限制 | 10000+ | 完全固定 |
| 中等限制 | 1000 | 允许小波动 |
| 弱限制 | 100 | 允许较大波动 |

## 逐步释放 / Gradual Release

平衡策略：

1. 第一阶段：强限制 (1000 kJ/mol/nm²)
2. 第二阶段：中等限制 (100 kJ/mol/nm²)
3. 第三阶段：无限制

## 参考资料 / References

- GROMACS 限制: https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html
- LSP 节点: `PositionRestraintsSubsection`, `PositionRestraintsEntry`
