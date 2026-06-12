# 自由能计算 / Free Energy Calculations

## 概述 / Overview

GROMACS 支持多种自由能计算方法，用于评估分子结合、溶剂化、突变等过程的热力学性质。

## 方法类型 / Method Types

### 1. 热力学积分 / Thermodynamic Integration (TI)

```mdp
free-energy = yes
init-lambda = 0.0
delta-lambda = 0.05
nstdhdl = 10
```

### 2. 自由能微扰 / Free Energy Perturbation (FEP)

```mdp
free-energy = yes
init-lambda = 0.0
delta-lambda = 0.05
nstdhdl = 10
calc-lambda-neighbors = -1    ; FEP
```

### 3. 扩展系综 / Expanded Ensemble

```mdp
free-energy = yes
init-lambda = 0.0
delta-lambda = 0.05
nstdhdl = 10
dfhist-lambda = 0.05
```

### 4. BAR / Bennett Acceptance Ratio

使用 MBAR 分析多个 λ 窗口的结果。

## Lambda 耦合 / Lambda Coupling

### 耦合参数 / Coupling Parameters

```mdp
; 范德华
couple-lambda0 = vdw-q
couple-lambda1 = vdw-q

; 库仑
couple-intramol = yes
```

### 软核势 / Soft-core Potentials

```mdp
; 防止奇异点
sc-alpha = 0.5
sc-power = 1
sc-sigma = 0.3
```

## 状态设定 / State Setup

### Alchemical 变化 / Alchemical Transformations

```mdp
init-lambda-state = 0          ; 初始状态
fep-lambdas = 0.0 0.05 0.1 ... 1.0  ; λ 窗口
```

每个 λ 窗口需要单独运行。

## 约束模拟 / Restrained Simulations

### 定位限制 / Position Restraints

用于控制配体-蛋白质距离：

```mdp
pull = yes
pull-coord1-type = umbrella
pull-coord1-geometry = distance
pull-coord1-k = 1000
```

### 方向限制 / Orientation Restraints

```mdp
; 控制配体方向
orires-fit = yes
orires-fc = 1000
```

## 分析方法 / Analysis Methods

### TI 分析 / TI Analysis

```bash
gmx bar -f dhdl.xvg -o -oi TI
```

### BAR 分析 / BAR Analysis

```bash
gmx bar -f dhdl.xvg -o -obar
```

### MBAR 分析 / MBAR Analysis

使用外部工具 (alchemical-analysis, pymbar)。

## 典型工作流 / Typical Workflow

### 1. 准备拓扑 / Prepare Topology

为初始和终态创建拓扑文件：
- `topol_A.top` - 状态 A
- `topol_B.top` - 状态 B

### 2. 设置 λ 窗口 / Set λ Windows

```bash
# 为每个 λ 窗口创建目录
for lambda in 0.0 0.05 0.1 ... 1.0; do
    mkdir lambda_$lambda
done
```

### 3. 运行模拟 / Run Simulations

每个 λ 窗口独立运行：
```bash
gmx grompp -f md.mdp -c conf.gro -p topol.top -o tpr.tpr \
    -dl $lambda
gmx mdrun -deffnm md
```

### 4. 分析结果 / Analyze Results

```bash
gmx bar -f */dhdl.xvg -o -obar
```

## 常见应用 / Common Applications

### 1. 配体结合 / Ligand Binding

使用双热力学积分：
1. 耦合配体到复合物
2. 耦合配体到溶液
3. 差值 = 结合自由能

### 2. 残基突变 / Residue Mutation

氨基酸突变 (如 Ala → Gly)：
```mdp
; 定向突变
free-energy = yes
couple-moltype = Protein
couple-lambda0 = none
couple-lambda1 = vdw-q
couple-intramol = no
```

### 3. 溶剂化自由能 / Solvation Free Energy

1. 气相模拟
2. 溶液模拟
3. 差值 = 溶剂化自由能

## 精度考虑 / Accuracy Considerations

### 软核参数 / Soft-core Parameters

```mdp
sc-alpha = 0.5            ; 默认
sc-power = 1
sc-sigma = 0.3            ; 基于 LJ σ
```

### λ 采样 / λ Sampling

| 系统 | 推荐窗口数 |
|------|------------|
| 小分子 | 5-11 |
| 蛋白质突变 | 10-20 |
| 复杂系统 | 20+ |

## 参考资料 / References

- GROMACS 自由能: https://manual.gromacs.org/current/reference-manual/algorithms/free-energy-calculations.html
