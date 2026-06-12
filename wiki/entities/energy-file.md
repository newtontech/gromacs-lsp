# 能量文件 / Energy File (.edr)

## 概述 / Overview

EDR (Energy Data file) 格式存储模拟过程中的能量、温度、压力、密度等热力学量。

## 文件内容 / File Contents

EDR 文件包含多种能量项：

### 势能项 / Potential Energy Terms

- **Bond**: 键伸缩能
- **Angle**: 角弯曲能
- **Dihedral**: 二面角扭转能
- **LJ**: Lennard-Jones 势能
- **Coulomb**: 库仑静电能
- **Potential**: 总势能

### 动能项 / Kinetic Energy Terms

- **Kinetic-En**: 总动能
- **Temperature**: 系统温度

### 压力/体积项 / Pressure/Volume Terms

- **Pressure**: 系统压力
- **Volume**: 系统体积
- **Density**: 系统密度

### 约束项 / Constraint Terms

- **Constraint**: 约束能

## 提取能量数据 / Extracting Energy Data

### 基本提取 / Basic Extraction

```bash
gmx energy -f md.edr -o energy.xvg
```

交互式选择：
```
Select the terms you want from the list:
1  Potential
2  Kinetic-En
3  Total-Energy
4  Temperature
5  Pressure
...
```

### 提取特定项 / Extract Specific Terms

```bash
# 非交互式
echo "Potential" | gmx energy -f md.edr -o potential.xvg

# 多项
echo -e "Potential\nKinetic-En\nTemperature" | \
    gmx energy -f md.edr -o combined.xvg
```

## 常见分析 / Common Analyses

### 1. 能量守恒 / Energy Conservation

```bash
echo "Total-Energy" | gmx energy -f nve.edr -o total_energy.xvg
```

对于 NVE 模拟，总能量应守恒。

### 2. 温度检查 / Temperature Check

```bash
echo "Temperature" | gmx energy -f nvt.edr -o temperature.xvg
```

温度应稳定在目标值附近。

### 3. 压力检查 / Pressure Check

```bash
echo "Pressure" | gmx energy -f npt.edr -o pressure.xvg
```

压力应围绕目标值波动。

### 4. 密度检查 / Density Check

```bash
echo "Density" | gmx energy -f npt.edr -o density.xvg
```

密度应收敛到稳定值。

## MDP 输出控制 / MDP Output Control

```mdp
nstenergy = 1000            ; 能量输出间隔
nstlog = 1000               ; 日志输出间隔
```

## 图形格式 / Graphical Format

XVG 格式特点：
- 基础文本格式
- 可用 Grace/xmgrace 绘图
- 可转换为其他格式

### 转换为 CSV

```bash
# 使用 paste 处理
paste <(awk '{print $1}' energy.xvg) \
      <(awk '{print $2}' energy.xvg) > energy.csv
```

## 能量组分分析 / Energy Component Analysis

### 分解能量 / Decompose Energy

```bash
# 选择所有相关项
echo -e "Bond\nAngle\nDihedral\nLJ-SR\nCoulomb-SR\nPotential" | \
    gmx energy -f md.edr -o components.xvg
```

### 自由能计算 / Free Energy Calculation

对于热力学积分：

```bash
gmx energy -f md.edr -o dVdl-kB.xvg
```

## 能量漂移 / Energy Drift

### 检查漂移 / Check Drift

```bash
# 拟合趋势
gmx energy -f nve.edr -o total_energy.xvg
# 使用 xmgrace 查看趋势线
```

### 可接受漂移 / Acceptable Drift

| 模拟类型 | 可接受漂移 |
|----------|------------|
| NVE (保守) | < 0.01 kJ/mol/ps |
| NVT/NPT | 不适用 |

## 参考资料 / References

- GROMACS 能量文件: https://manual.gromacs.org/current/reference-manual/file-formats.html
