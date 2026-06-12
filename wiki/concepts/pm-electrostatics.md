# PME 静电学 / PME Electrostatics

## 概述 / Overview

PME (Particle Mesh Ewald) 是处理周期性系统中长程静电相互作用的标准方法，基于 Ewald 求和。

## 基本原理 / Basic Principle

PME 将库仑相互作用分为三部分：

```
E_total = E_real + E_reciprocal + E_correction
```

1. **实空间项**: 短程相互作用
2. **倒易空间项**: 长程相互作用 (FFT)
3. **校正项**: 自能和排除项

## MDP 设置 / MDP Settings

### 基本 PME / Basic PME

```mdp
coulombtype = PME
rcoulomb = 1.0            ; 实空间截断 (nm)
rcoulomb-switch = 0.9     ; Switch 函数开始距离
```

### PME 参数 / PME Parameters

```mdp
pme-order = 4             ; 插值阶数 (4-8)
fourierspacing = 0.12     ; FFT 网格间距 (nm)
```

## 截断与网格 / Cutoff and Grid

### 截断距离 / Cutoff Distance

```mdp
rcoulomb = 1.0            ; 通常 0.9-1.2 nm
```

**经验法则**: `rcoulomb` 应至少为 `rvdw`

### 网格设置 / Grid Settings

```mdp
# 自动计算
fourierspacing = 0.12     ; 默认

# 或直接指定
nkx = nky = nkz = 40      ; 网格点数
```

## PME 变体 / PME Variants

### 1. 标准 PME / Standard PME

```mdp
coulombtype = PME
```

最常用，平衡精度和速度。

### 2. PME-Switch / PME with Switch

```mdp
coulombtype = PME-Switch
rcoulomb-switch = 0.9
rcoulomb = 1.0
```

使用 switch 函数平滑截断。

### 3. PME-User / User-defined PME

```mdp
coulombtype = PME-User
```

允许自定义修正表。

## 其他方法 / Other Methods

### Ewald 求和 / Ewald Summation

```mdp
coulombtype = Ewald
rcoulomb = 1.0
ewald-rtol = 1e-5        ; 精度
```

纯 Ewald 方法，比 PME 慢。

### Reaction Field / Reaction Field

```mdp
coulombtype = Reaction-Field
rcoulomb = 1.0
epsilon-rf = 78.5        ; 介电常数
```

适用于简单系统。

### Cut-off / Simple Cutoff

```mdp
coulombtype = Cut-off
rcoulomb = 1.0
```

不推荐，精度差。

## 性能优化 / Performance Optimization

### 网格尺寸 / Grid Size

```mdp
# 平衡精度与速度
fourierspacing = 0.12     ; 默认
# 或 0.10-0.15
```

### PME 阶数 / PME Order

```mdp
pme-order = 4            ; 默认，好平衡
# pme-order = 8          ; 更高精度，更慢
```

### 负载平衡 / Load Balancing

```bash
# MPI + PME
gmx mdrun -deffnm md -ntomp 1 -np 4 -pme 0  # 专用 PME 节点
```

## 精度考虑 / Precision Considerations

### 实空间截断 / Real-space Cutoff

| 截断 | 精度 | 性能 |
|------|------|------|
| 0.9 nm | 低 | 快 |
| 1.0 nm | 中 | 中 |
| 1.2 nm | 高 | 慢 |

### 倒易空间精度 / Reciprocal Space Precision

```mdp
ewald-rtol = 1e-5        ; 默认
# ewald-rtol = 1e-6      ; 更高精度
```

## 特殊应用 / Special Applications

### 2D PME / 2D PME

用于膜系统：

```mdp
coulombtype = PME
pbc = xy                 ; 仅 XY 周期性
```

### Ewald 电解质 / Ewald Electrostatics

用于带电系统：

```mdp
coulombtype = Ewald
epsilon-surface = 0      ; 表面介电常数
```

## 常见问题 / Common Issues

### 1. "PME grid too large" 警告

**症状**: PME 网格过大

**解决**:
- 增大 `fourierspacing`
- 减小 `pme-order`

### 2. 性能问题 / Performance Issues

**症状**: PME 计算慢

**解决**:
- 减小 `fourierspacing`
- 降低 `pme-order`
- 使用 PME 专用节点

### 3. 精度问题 / Accuracy Issues

**症状**: 能量不守恒

**解决**:
- 增大 `rcoulomb`
- 降低 `ewald-rtol`
- 检查 `pme-order`

## 参考资料 / References

- GROMACS PME: https://manual.gromacs.org/current/reference-manual/algorithms/electrostatics.html
