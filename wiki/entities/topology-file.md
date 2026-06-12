# 拓扑文件 / Topology File (.top)

## 概述 / Overview

GROMACS 拓扑文件 (`.top`) 定义了模拟系统的完整分子拓扑结构，包括原子类型、电荷、质量、键合相互作用和非键合相互作用参数。

## 文件结构 / File Structure

```top
; 注释以分号开始
;
; 包含力场文件
#include "forcefield.itp"

[ defaults ]
; 默认非键合参数设置

[ atomtypes ]
; 原子类型定义

[ moleculetype ]
; 分子类型定义
; name    nrexcl

[ atoms ]
; 原子列表

[ bonds ]
; 键相互作用

[ pairs ]
; 1-4 相互作用

[ angles ]
; 角相互作用

[ dihedrals ]
; 二面角相互作用

[ system ]
; 系统名称

[ molecules ]
; 分子列表
```

## 主要部分 / Main Sections

### 1. [defaults]

定义默认非键合相互作用参数：

```top
[ defaults ]
; nbfunc  comb-rule  gen-pairs  fudgeLJ  fudgeQQ
1         2          yes        0.5      0.8333
```

### 2. [atomtypes]

定义原子类型及其基本属性：

```top
[ atomtypes ]
; name  bond.type  at.num  mass    charge  ptype  sigma    epsilon
C      CA         6       12.011  0.0     A      0.337    0.4184
```

### 3. [moleculetype]

定义分子类型和排除数：

```top
[ moleculetype ]
; name    nrexcl
SOL      2
```

### 4. [atoms]

定义分子中的所有原子：

```top
[ atoms ]
; nr  type  resnr  residue  atom   cgnr  charge   mass
1   OW    1      SOL      OW     1     -0.834   16.0
2   HW    1      SOL      HW1    1      0.417    1.008
```

### 5. [bonds]

定义键合相互作用：

```top
[ bonds ]
; ai   aj   funct   parameters
1     2    1       0.1  500000
```

### 6. [system]

系统描述：

```top
[ system ]
My protein in water
```

### 7. [molecules]

系统中的分子数量：

```top
[ molecules ]
; Compound    #mol
Protein_A     1
SOL           10000
```

## 条件编译 / Conditional Compilation

支持 `#ifdef`, `#ifndef`, `#else`, `#endif` 指令：

```top
#ifdef POSRES
#include "posres.itp"
#endif
```

## 解析器实现 / Parser Implementation

Python 实现在 `mdparser.topology.GromacsTopologyParser`：

```python
from mdparser import topology

parser = topology.GromacsTopologyParser(
    include_shared=True,
    include_blacklist=["forcefield.itp"]
)

with open("topol.top") as f:
    top = parser.read(f)
```

## 节点结构 / Node Structure

每个拓扑元素表示为节点 (Node)：

- `Include` - #include 指令
- `Define` - #define 指令
- `Condition` - #ifdef/#ifndef/#endif
- `MoleculetypeSection` - [moleculetype]
- `AtomsEntry` - 原子条目
- `BondsEntry` - 键条目
- 等等...

## 参考资料 / References

- GROMACS 拓扑格式: https://manual.gromacs.org/current/reference-manual/topologies/topology-file-formats.html
- 源文件: `/raw/assets/mdparser/topology.py`
- 节点定义: `/raw/assets/mdparser/_gmx_nodes.py`
