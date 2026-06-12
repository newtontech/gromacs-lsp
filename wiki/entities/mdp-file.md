# 模拟参数文件 / MDP File (.mdp)

## 概述 / Overview

MDP (Molecular Dynamics Parameters) 文件控制 GROMACS 模拟的所有参数设置，包括积分方法、时间步长、温度和压力耦合、输出频率等。

## 核心参数 / Core Parameters

### 积分器 / Integrator

```mdp
integrator = md        ; 分子动力学
; 或 steep (最速下降)
; 或 cg (共轭梯度)
; 或 l-bfgs
```

### 时间步长 / Time Step

```mdp
dt = 0.002             ; 时间步长 (ps)
nsteps = 500000        ; 总步数
```

### 温度耦合 / Temperature Coupling

```mdp
tcoupl = V-rescale     ; 耦合方法
tc-grps = Protein Water_Non_Water  ; 耦合组
tau_t = 0.5 0.5        ; 耦合常数 (ps)
ref_t = 300 300        ; 参考温度 (K)
```

### 压力耦合 / Pressure Coupling

```mdp
pcoupl = Parrinello-Rahman  ; 耦合方法
pcoupltype = isotropic
tau_p = 2.0            ; 耦合常数 (ps)
ref_p = 1.0            ; 参考压力 (bar)
compressibility = 4.5e-5  ; 压缩率 (1/bar)
```

### 非键合相互作用 / Non-bonded Interactions

```mdp
cutoff-scheme = Verlet
coulombtype = PME      ; 库仑处理方法
rcoulomb = 1.0         ; 库仑截断 (nm)
rvdw = 1.0             ; VdW 截断 (nm)
pbc = xyz              ; 周期性边界条件
```

### 约束 / Constraints

```mdp
constraints = h-bonds   ; 约束氢键
constraint-algorithm = LINCS
```

### 输出控制 / Output Control

```mdp
nstxout = 5000         ; 坐标输出间隔
nstvout = 5000         ; 速度输出间隔
nstenergy = 1000       ; 能量输出间隔
nstlog = 1000          ; 日志输出间隔
nstfout = 0            ; 力输出间隔 (0=禁用)
```

### 初始速度 / Initial Velocities

```mdp
gen-vel = yes          ; 从 Maxwell 分布生成速度
gen-temp = 300         ; 生成温度 (K)
```

## 常用场景配置 / Common Scenario Configurations

### 能量最小化 / Energy Minimization

```mdp
integrator = steep
nsteps = 50000
emtol = 1000           ; kJ/mol/nm
```

### NVT 平衡 / NVT Equilibration

```mdp
integrator = md
dt = 0.002
nsteps = 50000
tcoupl = V-rescale
tc-grps = Protein SOL
tau_t = 0.5 0.5
ref_t = 300 300
```

### NPT 平衡 / NPT Equilibration

```mdp
integrator = md
dt = 0.002
nsteps = 50000
tcoupl = V-rescale
pcoupl = Parrinello-Rahman
```

### 生产模拟 / Production Simulation

```mdp
integrator = md
dt = 0.002
nsteps = 50000000
nstxout-compressed = 5000
cutoff-scheme = Verlet
ns_type = grid
nstlist = 10
rlist = 1.0
```

## 参数验证 / Parameter Validation

LSP 提供以下 MDP 参数的验证：

- `integrator`: md, steep, cg, l-bfgs, md-vv, nm, 等
- `cutoff-scheme`: verlet, group
- `coulombtype`: PME, PME-Switch, Ewald, Reaction-Field, 等
- `constraints`: none, all-bonds, h-bonds, all-angles
- `tcoupl`: no, berendsen, nose-hoover, andersen, v-rescale
- `pcoupl`: no, berendsen, parrinello-rahman, mttk, c-rescale

## 悬停文档 / Hover Documentation

LSP 为 MDP 参数提供悬停提示：

```python
# 从 gromacs_lsp/hover.py:
_MDP_DOCS = {
    "integrator": "Integration method. Values: md, steep, cg, ...",
    "dt": "Time step for integration (ps). Type: float.",
    "tcoupl": "Temperature coupling method. Values: no, berendsen, ...",
    # ...
}
```

## 参考资料 / References

- GROMACS MDP 参数: https://manual.gromacs.org/current/user-guide/mdp-options.html
- LSP 实现: `/raw/assets/gromacs_lsp/hover.py`
