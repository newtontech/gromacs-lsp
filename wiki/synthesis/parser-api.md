# 拓扑解析器 API / Topology Parser API

## 概述 / Overview

`GromacsTopologyParser` 是 GROMACS 拓扑文件的核心解析器，支持读取、写入和操作拓扑结构。

## 类定义 / Class Definition

```python
from mdparser import topology

parser = topology.GromacsTopologyParser(
    ignore_comments=True,
    preprocess=True,
    include_local=True,
    include_shared=False,
    local_paths=None,
    use_relative_local_paths=True,
    shared_paths=None,
    use_default_shared_paths=True,
    include_blacklist=None,
    definitions=None,
    resolve_conditions=True,
    verbose=True,
    reset_counts=True
)
```

## 参数说明 / Parameters

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `ignore_comments` | bool | True | 忽略注释 |
| `preprocess` | bool | True | 预处理包含文件 |
| `include_local` | bool | True | 解析本地包含 |
| `include_shared` | bool | False | 解析共享包含 |
| `local_paths` | list | None | 本地搜索路径 |
| `use_relative_local_paths` | bool | True | 使用相对路径 |
| `shared_paths` | list | None | 共享搜索路径 |
| `use_default_shared_paths` | bool | True | 使用 GROMACS 默认路径 |
| `include_blacklist` | list | None | 排除的包含文件 |
| `definitions` | dict | None | 预定义变量 |
| `resolve_conditions` | bool | True | 解析条件块 |
| `verbose` | bool | True | 详细输出 |
| `reset_counts` | bool | True | 重置计数器 |

## 基本用法 / Basic Usage

### 读取拓扑文件 / Read Topology File

```python
parser = topology.GromacsTopologyParser()

with open("topol.top") as f:
    top = parser.read(f)
```

### 使用定义 / Using Definitions

```python
# 等价于 gmx grompp -DPOSRES
definitions = {"POSRES": True}

parser = topology.GromacsTopologyParser(
    definitions=definitions
)
```

### 包含文件控制 / Include File Control

```python
parser = topology.GromacsTopologyParser(
    include_shared=True,
    include_blacklist=["forcefield.itp"],
    shared_paths=["/path/to/forcefield"]
)
```

## 拓扑对象 / Topology Object

### 迭代节点 / Iterate Nodes

```python
for node in top:
    print(f"{node.value!r}")
```

### 访问节点 / Access Nodes

```python
# 按索引
node = top[0]

# 按键
node = top["some_key"]

# 切片
nodes = top[10:20]
```

### 添加节点 / Add Nodes

```python
from mdparser._gmx_nodes import AtomsEntry

entry = AtomsEntry(
    nr=1, type="CT", resnr=1,
    residue="ALA", atom="CA",
    cgnr=1, charge=0.0, mass=12.0
)

top.add("atom_1", entry)
```

### 删除节点 / Delete Nodes

```python
top.pop("atom_1")      # 删除并返回
top.discard("atom_1")  # 删除但不报错
```

### 替换节点 / Replace Nodes

```python
new_entry = AtomsEntry(...)
top.replace("atom_1", new_entry)
```

## 节点类型 / Node Types

### 基础节点 / Basic Nodes

```python
from mdparser._gmx_nodes import (
    Include,    # #include 指令
    Define,     # #define 指令
    Condition,  # #ifdef/#ifndef/#endif
    Comment,    # 注释
    Section,    # [section]
)
```

### 拓扑节点 / Topology Nodes

```python
from mdparser._gmx_nodes import (
    MoleculetypeSection,
    AtomsSubsection,
    BondsSubsection,
    AnglesSubsection,
    DihedralsSubsection,
    SystemSection,
    MoleculesSection,
)
```

### 条目节点 / Entry Nodes

```python
from mdparser._gmx_nodes import (
    AtomsEntry,
    BondsEntry,
    AnglesEntry,
    DihedralsEntry,
    MoleculetypeEntry,
    SystemEntry,
    MoleculesEntry,
)
```

## 输出拓扑 / Write Topology

```python
# 转换为字符串
topology_str = str(top)

# 写入文件
with open("output.top", "w") as f:
    f.write(str(top))
```

## 高级功能 / Advanced Features

### 查找互补条件 / Find Complementary Condition

```python
condition_node = top["some_condition"]
complement = top.find_complement(condition_node)
```

### 检查解析状态 / Check Parse Status

```python
# 是否所有包含都已解析？
if not top.includes_resolved:
    print("存在未解析的包含")

# 是否所有条件都已解析？
if not top.conditions_resolved:
    print("存在未解析的条件")
```

## 参考资料 / References

- 源代码: `/raw/assets/mdparser/topology.py`
- 节点定义: `/raw/assets/mdparser/_gmx_nodes.py`
- 任务工具: `/raw/assets/mdparser/tasks.py`
