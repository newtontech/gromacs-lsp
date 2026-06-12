# 增强采样技术 / Enhanced Sampling Techniques

> 类型：概念
> 学科/领域：分子动力学 / 增强采样
> 创建日期：2026-06-12
> 来源：raw/assets/gromacs-mdp-complete-reference.md

## 定义 / Definition

增强采样技术是一类加速分子动力学模拟中构象空间探索的方法，用于克服常规 MD 难以跨越的高能垒问题。

## GROMACS 内置方法 / Built-in Methods

### 1. AWH (Adaptive Weighted Histogram)

GROMACS 内置的自适应偏置方法，自动沿反应坐标施加偏置并估计 PMF。

```mdp
awh = yes
awh1-dim1-coord-provider = pull
awh1-dim1-start = 0.5       ; nm
awh1-dim1-end = 3.5         ; nm
awh1-dim1-force-constant = 1000
awh1-dim1-diffusion = 1e-5
```

特点：
- 自动调整偏置强度
- 支持1D和2D PMF
- 支持多 walker 共享偏置
- 支持自由能 lambda 维度

### 2. 拉伸动力学 (Steered MD)

通过 Pull 代码施加外力：

```mdp
pull = yes
pull-coord1-type = umbrella
pull-coord1-rate = 0.01      ; nm/ps
pull-coord1-k = 1000
```

### 3. 伞状采样 (Umbrella Sampling)

沿反应坐标在不同位置施加简谐约束：

```mdp
pull-coord1-type = umbrella
pull-coord1-k = 1000
pull-coord1-init = 1.0       ; 参考位置
```

然后用 WHAM 分析：
```bash
gmx wham -it tpr-files.dat -if pullf-files.dat -o pmf.xvg
```

### 4. 副本交换 (Replica Exchange)

参见 [[副本交换 / Replica Exchange]]

### 5. 膨胀系综 (Expanded Ensemble)

```mdp
free-energy = expanded
lmc-stats = wang-landau
lmc-mc-move = metropolis-transition
```

### 6. 模拟退火 (Simulated Annealing)

```mdp
annealing = single
annealing-npoints = 3
annealing-time = 0 3 6
annealing-temp = 298 280 270
```

### 7. 模拟回火 (Simulated Tempering)

```mdp
simulated-tempering = yes
sim-temp-low = 300
sim-temp-high = 400
simulated-tempering-scaling = geometric
```

## 外部工具集成 / External Tool Integration

### PLUMED

GROMACS 支持与 PLUMED 联合使用进行高级增强采样：

```bash
gmx mdrun -plumed plumed.dat
```

PLUMED 提供：
- Well-tempered metadynamics
- Variationally enhanced sampling (VES)
- 多种集体变量定义
- OPES (On-the-fly Probability Enhanced Sampling)

### Colvars 模块

GROMACS 内置 Colvars 集体变量模块：

```mdp
colvars-active = true
colvars-configfile = colvars.in
```

## 选择指南 / Selection Guide

| 方法 | 适用场景 | 计算成本 |
|------|---------|---------|
| AWH | 自动 PMF 计算 | 中等 |
| 伞状采样 | 已知反应坐标 | 高（多窗口）|
| REMD | 全局构象采样 | 高（多副本）|
| Metadynamics | 复杂 CV | 中等 |
| 模拟退火 | 结构优化 | 低 |

## 相关概念 / Related Concepts

- [[副本交换 / Replica Exchange]]
- [[自由能计算 / Free Energy Calculations]]
- [[Pull 代码 / Pull Code]]

## 来源 / References

- GROMACS MDP 选项: https://manual.gromacs.org/current/user-guide/mdp-options.html
- PLUMED 文档: https://www.plumed.org/doc-v2.9/user-doc/html/tutorials.html
- 原始资料: `/raw/assets/gromacs-mdp-complete-reference.md`
