# 非键合相互作用 / Non-bonded Interactions

## 概述 / Overview

非键合相互作用描述非直接相连原子之间的相互作用，主要包括范德华力 (Lennard-Jones) 和静电相互作用。

## 相互作用类型 / Interaction Types

### 1. Lennard-Jones 势 / Lennard-Jones Potential

范德华力的标准模型：

```
V(r) = 4ε[(σ/r)¹² - (σ/r)⁶]
```

或等效形式：

```
V(r) = C12/r¹² - C6/r⁶
```

### 2. 库仑相互作用 / Coulomb Interaction

静电相互作用：

```
V(r) = (qi * qj) / (4πε₀εr)
```

## 处理方法 / Treatment Methods

### 截断方案 / Cutoff Schemes

```mdp
cutoff-scheme = Verlet    ; 推荐
cutoff-scheme = Group     ; 已弃用
```

### 库仑处理方法 / Coulomb Methods

| 方法 | 描述 | 参数 |
|------|------|------|
| PME | 粒子网格 Ewald | `rcoulomb`, `pme-order` |
| PME-Switch | 带 switch 的 PME | `rcoulomb`, `rcoulomb-switch` |
| Ewald | 标准 Ewald | `ewald-rtol`, `ewald-geometry` |
| Reaction-Field | 反应场 | `rcoulomb`, `epsilon-rf` |
| Cut-off | 简单截断 | `rcoulomb` |

### PME 设置 / PME Settings

```mdp
coulombtype = PME
rcoulomb = 1.0
rcoulomb-switch = 0.9      ; 如果使用 PME-Switch
pbc = xyz
fourierspacing = 0.12
```

### Lennard-Jones 处理 / Lennard-Jones Treatment

```mdp
vdwtype = Cut-off          ; 或 PME, Switch
rvdw = 1.0
rvdw-switch = 0.9          ; 如果使用 Switch
```

## 邻区列表 / Neighbor List

```mdp
nstlist = 10               ; 更新频率
rlist = 1.0                ; 邻区列表截断
ns_type = grid             ; 或 simple
```

## 组合规则 / Combination Rules

### [defaults] 部分 / [defaults] Section

```top
[ defaults ]
; nbfunc  comb-rule  gen-pairs  fudgeLJ  fudgeQQ
1         2          yes        0.5      0.8333
```

### 组合规则类型 / Combination Rule Types

| comb-rule | 描述 | 公式 |
|-----------|------|------|
| 1 | Lorentz-Berthelot | σij = (σi+σj)/2, εij = √(εiεj) |
| 2 | 几何平均 | σij = √(σiσj), εij = √(εiεj) |
| 3 | 算术平均 (仅 ε) | σij = (σi+σj)/2, εij = (εi+εj)/2 |

## 1-4 相互作用 / 1-4 Interactions

被两个键分隔的原子间相互作用：

```top
[ pairs ]
; ai   aj   funct   fudgeLJ  fudgeQQ
1     5    1       0.5      0.8333
```

- `fudgeLJ`: LJ 相互作用缩放因子
- `fudgeQQ`: 电荷相互作用缩放因子

## 排除 / Exclusions

排除特定原子对的非键合相互作用：

```top
[ exclusions ]
; atom indices
1    2    3    4
```

通常：
- `nrexcl = 1`: 排除 1-2 相互作用 (直接相连)
- `nrexcl = 2`: 排除 1-2 和 1-3 相互作用
- `nrexcl = 3`: 排除 1-2, 1-3, 和 1-4 相互作用

## 温度控制 / Temperature Control

### 积分方法 / Integration Methods

```mdp
tcoupl = V-rescale         ; 推荐
tcoupl = Berendsen         ; 快速但不精确
tcoupl = Nose-Hoover       ; 正则系综
tcoupl = Andersen          ; 随机
```

### 分组 / Groups

```mdp
tc-grps = Protein Water_Non_Water
tau_t = 0.5 0.5
ref_t = 300 300
```

## 压力控制 / Pressure Control

### 积分方法 / Integration Methods

```mdp
pcoupl = Parrinello-Rahman  ; 正则系综
pcoupl = Berendsen          ; 快速但不精确
pcoupl = C-rescale          ; 恒压模拟
```

### 参数 / Parameters

```mdp
pcoupltype = isotropic
tau_p = 2.0
ref_p = 1.0
compressibility = 4.5e-5
```

## 参考资料 / References

- GROMACS 非键合相互作用: https://manual.gromacs.org/current/reference-manual/algorithms/interactions.html
