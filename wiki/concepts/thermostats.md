# 恒温器 / Thermostats

## 概述 / Overview

恒温器用于控制分子动力学模拟中的系统温度，模拟与热浴的耦合。

## 常见恒温器 / Common Thermostats

### 1. Berendsen 恒温器 / Berendsen Thermostat

```mdp
tcoupl = Berendsen
tau_t = 0.5              ; 耦合常数 (ps)
ref_t = 300              ; 参考温度 (K)
```

**特点**:
- 快速达到目标温度
- 不产生正确的正则系综
- 适合初步平衡

**耦合方程**:
```
T(t+dt) = T(t) + λ(T0 - T(t))
```

### 2. V-rescale (Velocity Rescale)

```mdp
tcoupl = V-rescale
tau_t = 0.5
ref_t = 300
```

**特点**:
- 产生正确的正则系综
- 比 Berendsen 稍慢
- 推荐用于生产模拟
- GROMACS 推荐选择

### 3. Nose-Hoover 恒温器 / Nose-Hoover Thermostat

```mdp
tcoupl = Nose-Hoover
tau_t = 0.5
ref_t = 300
```

**特点**:
- 严格的正则系综
- 可能产生振荡
- 适合精确模拟

**链长**:
```mdp
nhsct = 10               ; Nose-Hoover 链长 (高级)
```

### 4. Andersen 恒温器 / Andersen Thermostat

```mdp
tcoupl = Andersen
tau_t = 0.5
ref_t = 300
```

**特点**:
- 随机选择原子重新分配速度
- 产生正确的正则系综
- 不适合连续时间相关函数

## 温度分组 / Temperature Groups

### 单组 / Single Group

```mdp
tc-grps = System
tau_t = 0.5
ref_t = 300
```

### 多组 / Multiple Groups

```mdp
tc-grps = Protein Water_Non_Water
tau_t = 0.5 0.5
ref_t = 300 300
```

### 不同温度 / Different Temperatures

```mdp
tc-grps = Protein Solvent
tau_t = 0.5 0.5
ref_t = 300 350
# 溶剂温度更高
```

## 耦合常数 / Coupling Constant

### tau_t 选择 / tau_t Selection

| 值 | 效果 | 用途 |
|----|------|------|
| 0.1 | 强耦合 | 快速平衡 |
| 0.5 | 中等耦合 | 标准 |
| 1.0+ | 弱耦合 | 精确模拟 |

**经验法则**: `tau_t` 应至少为 10 × `dt`

## 特殊技术 / Special Techniques

### 温度群分离 / Temperature Group Separation

对于膜蛋白-脂质系统：

```mdp
tc-grps = Protein_Lipid Water
tau_t = 0.5 0.5
ref_t = 310 310
```

### 局部加热 / Local Heating

用于热导率计算：

```mdp
tc-grps = Hot_Middle Cold_Middle
tau_t = 0.5 0.5
ref_t = 350 300
```

## 监控温度 / Monitoring Temperature

```bash
gmx energy -f md.edr -o temperature.xvg
# 选择 Temperature
```

### 温度波动 / Temperature Fluctuation

预期波动：
```
σ(T) ≈ sqrt(kB T² / CV)
```

对于小系统波动较大。

## 常见问题 / Common Issues

### 1. 温度漂移 / Temperature Drift

**症状**: 温度持续偏离目标

**解决**:
- 检查 `tau_t`
- 验证热浴耦合
- 检查时间步长

### 2. 温度振荡 / Temperature Oscillation

**症状**: 温度大幅波动

**解决**:
- 增大 `tau_t`
- 减小 `dt`
- 使用 Berendsen

### 3. 不同组温度不同 / Different Group Temperatures

**症状**: 各组温度不一致

**解决**:
- 检查分组是否合理
- 验证热容量
- 调整 `tau_t`

## 参考资料 / References

- GROMACS 恒温器: https://manual.gromacs.org/current/reference-manual/algorithms/thermostats.html
