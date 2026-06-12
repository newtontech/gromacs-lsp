# 副本交换分子动力学 / Replica Exchange Molecular Dynamics (REMD)

> 类型：概念
> 学科/领域：分子动力学 / 增强采样
> 创建日期：2026-06-12
> 来源：raw/assets/gromacs-remd.md

## 定义 / Definition

副本交换分子动力学 (REMD) 是一种增强采样方法，通过在不同温度下运行多个副本并定期交换状态来加速构象空间的探索，特别适用于跨越高能垒的采样。

## 核心机制 / Core Mechanism

### 交换概率 / Exchange Probability

```
P(1 <-> 2) = min(1, exp[(1/kB*T1 - 1/kB*T2)(U1 - U2)])
```

- T1, T2：参考温度
- U1, U2：瞬时势能
- 交换后速度缩放：`(T1/T2)^{+/-0.5}`

### 温度选择 / Temperature Selection

温度间距的指导原则：

```
epsilon ~ 1/sqrt(N_atoms)
```

- 自由度：`N_df ~ 2 * N_atoms`（所有键约束时）
- 典型交换概率：20-25%
- 工具：https://virtualchemistry.org/remd-temperature-generator/

### 交换策略 / Exchange Strategy

GROMACS 使用交替奇偶对交换：
- 奇数步：奇数对 (0-1, 2-3, ...)
- 偶数步：偶数对 (1-2, 3-4, ...)

## REMD 变体 / REMD Variants

### 1. 温度 REMD (T-REMD)

最常见形式，不同温度的副本之间交换。

### 2. 哈密顿量 REMD (H-REMD)

每个副本有不同的哈密顿量（通过 lambda 值定义）：

```
P(1 <-> 2) = min(1, exp[(1/kB*T)(U1(x1) - U1(x2) + U2(x2) - U2(x1))])
```

### 3. 等温等压 REMD

扩展交换概率包含体积项 (Okabe et al.)。

### 4. Gibbs 采样 REMD

测试所有可能的对交换（不仅限邻居），提高效率但有额外通信开销。

## 运行配置 / Running Configuration

```bash
# 生成不同温度的 tpr 文件
gmx grompp -f nvt_300.mdp -o topol_300.tpr
gmx grompp -f nvt_310.mdp -o topol_310.tpr

# 使用 MPI 运行
mpirun -np N gmx_mpi mdrun -s topol.tpr \
    -multidir sim0 sim1 sim2 ... simN \
    -replex 1000   ; 交换间隔（步数）
```

### 要求 / Requirements

- 必须安装 MPI
- 每个副本运行在独立 rank 上
- 温度间距需仔细选择

## 分析 / Analysis

```bash
# 提取温度数据
gmx energy -f sim*/ener.edr -o temperature.xvg

# 检查交换率
grep "Repl  average" md.log
```

## 应用场景 / Applications

- 蛋白质折叠研究
- 多肽构象采样
- 配体结合模式探索
- 相变研究

## 相关概念 / Related Concepts

- [[自由能计算 / Free Energy Calculations]]
- [[恒温器 / Thermostats]]
- [[Pull 代码 / Pull Code]]
- [[能量最小化 / Energy Minimization]]

## 来源 / References

- GROMACS 手册: https://manual.gromacs.org/2026.2/reference-manual/algorithms/replica-exchange.html
- 原始资料: `/raw/assets/gromacs-remd.md`
