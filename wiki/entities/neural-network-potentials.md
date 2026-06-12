# 神经网络势 / Neural Network Potentials (NNP)

> 类型：实体
> 创建日期：2026-06-12
> 来源：raw/assets/gromacs-mdp-complete-reference.md

## 简介 / Introduction

GROMACS 2026+ 支持通过 NNPot 接口集成神经网络势（NNP），实现混合 NNP/MM（神经网络势/分子力学）模拟。需要 LibTorch 支持。

## MDP 配置 / MDP Configuration

```mdp
nnpot-active = true
nnpot-modelfile = model.pt           ; TorchScript 模型
nnpot-input-group = System           ; NNP 原子组
nnpot-embedding = mechanical          ; 或 electrostatic-model
```

### 嵌入方案 / Embedding Schemes

- `mechanical` — NNP-MM 相互作用由经典力场处理
- `electrostatic-model` — NNP-MM 相互作用由 NNP 模型处理（模型需返回 MM 原子上的力）

### 模型输入 / Model Inputs

支持最多 9 个输入字段：

| 输入名 | 描述 |
|--------|------|
| `atom-positions` | NNP 原子位置 |
| `atom-numbers` | 原子序数 |
| `atom-pairs` | NNP 原子对（需 pair-cutoff） |
| `pair-shifts` | 周期性位移向量 |
| `atom-positions-mm` | MM 原子位置 |
| `atom-charges-mm` | MM 原子电荷 |
| `nnp-charge` | NNP 总电荷 |
| `box` | 模拟盒向量 |
| `pbc` | 周期性边界条件 |

### 链接原子 / Link Atoms

```mdp
nnpot-link-type = H           ; 链接原子类型（默认 H）
nnpot-link-distance = 0.1     ; nm，链接原子到 MM 原子距离
```

## 相关概念 / Related Concepts

- [[QMMM 模拟 / QMMM Simulation]]
- [[力场 / Force Field]]

## 来源 / References

- GROMACS MDP 选项: https://manual.gromacs.org/current/user-guide/mdp-options.html
