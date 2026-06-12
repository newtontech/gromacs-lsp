# QMMM 模拟 / QMMM Simulation

## 概述 / Overview

QMMM (Quantum Mechanics/Molecular Mechanics) 是一种混合模拟方法，结合了：

- **QM 区域**: 用量子力学处理 (高精度，计算昂贵)
- **MM 区域**: 用分子力学处理 (较低精度，快速)

## 应用场景 / Applications

1. **化学反应研究**: 反应机理、过渡态
2. **酶催化**: 酶活性位点
3. **电子转移**: 电荷转移过程
4. **光谱性质**: 电子激发、光谱计算

## GROMACS QMMM 实现 / GROMACS QMMM Implementation

### 拓扑文件 / Topology File

```top
[ moleculetype ]
; name    nrexcl
QMMM_model  3

[ atoms ]
; nr  type  resnr  residue  atom  cgnr  charge  mass
1    M    1      QM       QM    1     0.0    0.0
```

### QMMM 限制 / QMMM Restraints

```top
[ position_restraints ]
; QM 区域原子需要强限制
1    1    10000  10000  10000
```

## 测试文件 / Test Files

### QMMM 拓扑示例 / QMMM Topology Examples

项目包含多个 QMMM 测试文件：

1. `qmmm.top` - 基本 QMMM 拓扑
2. `qmmm_tip4p.top` - TIP4P 水模型的 QMMM
3. `qmmm_water.top` - 水分子的 QMMM

## 节点类型 / Node Types

LSP 支持 QMMM 相关节点：

```python
# 从 mdparser/_gmx_nodes.py:
class PositionRestraintsEntry(P1TermEntry):
    _node_key_name = "position_restraints_entry"
```

## 典型工作流 / Typical Workflow

### 1. 准备 QMMM 拓扑

```python
from mdparser import tasks, topology

parser = topology.GromacsTopologyParser(
    include_shared=True,
    definitions={"QMMM": True}
)

with open("qmmm.top") as f:
    top = parser.read(f)
```

### 2. 合并分子 / Merge Molecules

```python
# 合并 QM 和 MM 分子
from mdparser import tasks

merged = tasks.merge_molecules(qm_mol, mm_mol)
```

### 3. 设置 QMMM 限制

```top
#ifdef QMMM
[ position_restraints ]
; QM 原子需要强限制以防止漂移
1    1    10000  10000  10000
#endif
```

## 常见问题 / Common Issues

### 1. 原子漂移 / Atom Drift

**解决方案**: 使用强位置限制

```top
fc = 10000  ; kJ/mol/nm²
```

### 2. 边界效应 / Boundary Effects

**解决方案**: 添加缓冲区域

### 3. 电荷匹配 / Charge Matching

确保 QM 和 MM 区域的总电荷匹配。

## QMMM 软件接口 / QMMM Software Interfaces

GROMACS 支持与多种 QMMM 软件接口：

- **Gaussian**: 最常用
- **ORCA**: 免费替代
- **MOPAC**: 半经验方法
- **CP2K**: 开源

## 参考资料 / References

- GROMACS QMMM: https://manual.gromacs.org/current/reference-manual/algorithms/qmmm.html
- 测试文件: `/raw/assets/test/test_tasks/`
