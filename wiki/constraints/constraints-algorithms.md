# 约束算法 / Constraint Algorithms

## 概述 / Overview

约束算法用于固定某些原子间距离，允许更大的时间步长并减少高频振动模式。

## 为什么使用约束？ / Why Use Constraints?

1. **允许更大时间步长**: 氢键振动频率高 (~10 fs 时间步长)，约束后可用 2 fs
2. **减少自由度**: 消除快速振动模式
3. **提高效率**: 更快的模拟

## 约束类型 / Constraint Types

### 1. 氢键约束 / Hydrogen Bonds

```mdp
constraints = h-bonds
```

- 约束所有与氢连接的重原子键
- 允许 2 fs 时间步长
- 最常用

### 2. 全键约束 / All Bonds

```mdp
constraints = all-bonds
```

- 约束所有键
- 允许更大时间步长
- 可能影响某些性质

### 3. 全角度约束 / All Angles

```mdp
constraints = all-angles
```

- 约束所有键和角度
- 非常严格
- 很少使用

## 约束算法 / Constraint Algorithms

### LINCS (Linear Constraint Solver)

```mdp
constraint-algorithm = LINCS
```

**特点**:
- 稳定、快速
- 适合并行计算
- GROMACS 默认

**参数**:
```mdp
lincs-order = 4           ; 约束阶数
lincs-iter = 1            ; 迭代次数
lincs-wangle = 30         ; 警告角度
```

### SHAKE

```mdp
constraint-algorithm = SHAKE
```

**特点**:
- 经典算法
- 比 LINCS 慢
- 与 CHARMM 兼容

## SETTLE 算法 / SETTLE Algorithm

专门用于水分子的刚性约束：

```top
[ settles ]
; i   funct   dOH     dHH
1    1       0.09572 0.15139
```

**特点**:
- 精确解析解
- 非常快
- 自动应用于 3 原子水模型

## 约束与质量 / Constraints and Masses

约束原子需要调整质量以保持正确的动能：

```mdp
; LINCS 自动调整质量
; 对于 hydrogen mass partitioning:
constraint-algorithm = LINCS
```

## 时间步长限制 / Timestep Limitations

| 约束类型 | 最大时间步长 |
|----------|--------------|
| 无约束 | 0.5-1 fs |
| h-bonds | 2 fs |
| all-bonds | 2-4 fs |
| all-angles | 4-5 fs |

## 常见问题 / Common Issues

### 1. LINCS 警告 / LINCS Warnings

**症状**:
```
Step 1000, time 2.000 ps: LINCS warning
```

**解决**:
- 减小 `dt`
- 增大 `lincs-order`
- 增大 `lincs-iter`

### 2. 约束冲突 / Constraint Conflicts

**症状**: 模拟崩溃

**解决**:
- 检查拓扑文件中的约束定义
- 确保无循环约束
- 验证初始结构

### 3. 能量漂移 / Energy Drift

**症状**: 总能量不稳定

**解决**:
- 减小 `dt`
- 检查约束精度
- 增大 `lincs-iter`

## 氢质量重新分配 / Hydrogen Mass Repartitioning

允许更大的时间步长：

```mdp
; 将氢质量增加到 4 amu
; 相应减少重原子质量
constraints = h-bonds
dt = 0.004              ; 4 fs 时间步长
```

## 参考资料 / References

- GROMACS 约束: https://manual.gromacs.org/current/reference-manual/algorithms/constraints.html
- LSP 节点: `ConstraintsSubsection`, `ConstraintsEntry`, `SettlesSubsection`, `SettlesEntry`
