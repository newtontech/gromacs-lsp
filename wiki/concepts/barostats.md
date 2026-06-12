# 恒压器 / Barostats

## 概述 / Overview

恒压器用于控制分子动力学模拟中的系统压力，模拟与压力浴的耦合，实现等压系综 (NPT)。

## 常见恒压器 / Common Barostats

### 1. Berendsen 恒压器 / Berendsen Barostat

```mdp
pcoupl = Berendsen
tau_p = 2.0              ; 耦合常数 (ps)
ref_p = 1.0              ; 参考压力 (bar)
compressibility = 4.5e-5  ; 压缩率 (1/bar)
```

**特点**:
- 快速达到目标压力
- 不产生正确的等压系综
- 适合初步平衡
- 稳定性好

### 2. Parrinello-Rahman 恒压器 / Parrinello-Rahman Barostat

```mdp
pcoupl = Parrinello-Rahman
tau_p = 2.0
ref_p = 1.0
compressibility = 4.5e-5
```

**特点**:
- 产生正确的等压系综
- 可能产生振荡
- 推荐用于生产模拟

### 3. MTTK 恒压器 / MTTK Barostat

```mdp
pcoupl = MTTK
tau_p = 2.0
ref_p = 1.0
```

**特点**:
- Martyna-Tuckerman-Tobias-Klein 方法
- 与 Nose-Hoover 配合良好

### 4. C-rescale 恒压器 / C-rescale Barostat

```mdp
pcoupl = C-rescale
tau_p = 2.0
ref_p = 1.0
```

**特点**:
- 速度重新缩放方法
- 类似 V-rescale 恒温器

## 压力耦合类型 / Pressure Coupling Types

### 各向同性 / Isotropic

```mdp
pcoupltype = isotropic
```

- 所有方向耦合相同
- 适合液体、立方盒子

### 半各向同性 / Semi-isotropic

```mdp
pcoupltype = semiisotropic
```

- XY 平面与 Z 方向不同
- 适合膜系统

### 各向异性 / Anisotropic

```mdp
pcoupltype = anisotropic
```

- 每个方向独立耦合
- 适合晶格系统

### 表面张力 / Surface Tension

```mdp
pcoupltype = surface
```

- 膜系统表面张力控制

## 压缩率 / Compressibility

### 典型值 / Typical Values

| 系统 | 压缩率 (1/bar) |
|------|----------------|
| 水 | 4.5e-5 |
| 蛋白质 | ~1e-5 |
| 膜 | ~1e-5 |

```mdp
compressibility = 4.5e-5   ; 水
```

## 盒子变形 / Box Deformation

### 各向同性变形 / Isotropic Deformation

```
d(ln V)/dt = (V0 - V)/(τ_p V)
```

### 半各向同性 / Semi-isotropic Deformation

```mdp
; XY 平面独立于 Z 方向
pcoupltype = semiisotropic
compressibility = 4.5e-5 4.5e-5
```

## 耦合常数 / Coupling Constant

### tau_p 选择 / tau_p Selection

| 值 | 效果 | 用途 |
|----|------|------|
| 0.5 | 强耦合 | 快速平衡 |
| 2.0 | 中等耦合 | 标准 |
| 5.0+ | 弱耦合 | 精确模拟 |

**经验法则**: `tau_p` 应至少为 20 × `dt`

## 特殊应用 / Special Applications

### 膜系统 / Membrane Systems

```mdp
pcoupl = Parrinello-Rahman
pcoupltype = semiisotropic
tau_p = 2.0
ref_p = 1.0 1.0          ; XY 和 Z 方向
compressibility = 4.5e-5 4.5e-5
```

### 表面张力模拟 / Surface Tension

```mdp
pcoupl = Parrinello-Rahman
pcoupltype = surface
ref_p = 1.0
ref_surface_tension = 0.0  ; mN/m
```

## 监控压力 / Monitoring Pressure

```bash
gmx energy -f md.edr -o pressure.xvg
# 选择 Pressure
```

### 压力分量 / Pressure Components

```bash
# 压力张量
gmx energy -f md.edr
# 选择 Pres-XX, Pres-YY, Pres-ZZ
```

## 监控密度 / Monitoring Density

```bash
gmx energy -f md.edr -o density.xvg
# 选择 Density
```

### 收敛标准 / Convergence Criteria

- 水系统: ~1000 kg/m³
- 膜系统: ~1020 kg/m³
- 蛋白质系统: 取决于含水量

## 常见问题 / Common Issues

### 1. 压力不稳定 / Pressure Unstable

**症状**: 压力大幅波动

**解决**:
- 增大 `tau_p`
- 使用 Berendsen
- 检查盒子尺寸

### 2. 密度不收敛 / Density Not Converging

**症状**: 密度持续变化

**解决**:
- 延长平衡时间
- 检查耦合类型
- 验证压缩率

### 3. 盒子崩溃 / Box Collapse

**症状**: 盒子维度急剧减小

**解决**:
- 使用位置限制
- 减小压力耦合强度
- 检查初始结构

## 参考资料 / References

- GROMACS 恒压器: https://manual.gromacs.org/current/reference-manual/algorithms/barostats.html
