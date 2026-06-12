# 多时间步长 / Multiple Time Stepping (MTS)

> 类型：概念
> 学科/领域：分子动力学 / 性能优化
> 创建日期：2026-06-12
> 来源：raw/assets/gromacs-mdp-complete-reference.md

## 定义 / Definition

多时间步长 (MTS) 是一种将不同力以不同频率计算的优化策略，减少昂贵的长程力计算次数。

## GROMACS MDP 设置 / MDP Configuration

```mdp
mts = yes
mts-levels = 2
mts-level2-forces = longrange-nonbonded
mts-level2-factor = 2
```

### 可选 Level 2 力组 / Available Level 2 Force Groups

- `longrange-nonbonded` — PME/Ewald 长程力（默认）
- `nonbonded` — 所有非键合力
- `pair` — 列表对力（如 1-4）
- `dihedral` — 所有二面角（含 cmap）
- `angle` — 角相互作用
- `pull` — Pull 代码力
- `awh` — AWH 偏置力

### 限制 / Limitations

- 仅支持 `integrator = md`（leap-frog）
- Level 2 因子通常为 2-4
- AWH 和 Pull 必须在同一 MTS 层级

## 质量重分配 / Mass Repartitioning

与 MTS 配合使用，缩轻原子质量以允许更大时间步：

```mdp
mass-repartition-factor = 3    ; 氢原子质量 x3
; 约束 = h-bonds 时，可使用 4 fs 时间步
```

## 性能影响 / Performance Impact

| 配置 | 时间步 | 加速比 |
|------|--------|--------|
| 默认 (无 MTS) | 2 fs | 1x |
| MTS + mass repartition | 4 fs | ~1.5-2x |

## 相关概念 / Related Concepts

- [[MDP 文件 / MDP File]]
- [[PME 静电学 / PME Electrostatics]]

## 来源 / References

- GROMACS MDP 选项: https://manual.gromacs.org/current/user-guide/mdp-options.html
- 原始资料: `/raw/assets/gromacs-mdp-complete-reference.md`
