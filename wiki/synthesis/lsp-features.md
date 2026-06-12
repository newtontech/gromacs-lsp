# LSP 功能 / LSP Features

## 概述 / Overview

gromacs-lsp 为 GROMACS 文件提供语言服务器支持，包括语法高亮、自动补全、诊断和悬停文档。

## 支持的文件格式 / Supported File Formats

| 格式 | 扩展名 | 功能 |
|------|--------|------|
| 拓扑文件 | `.top`, `.itp` | 解析、补全、诊断 |
| 参数文件 | `.mdp` | 补全、验证 |
| 坐标文件 | `.gro` | 解析、验证 |

## 补全功能 / Completion Features

### MDP 参数补全 / MDP Parameter Completion

```python
# 从 gromacs_lsp/completion.py
def mdp_completions() -> list[dict[str, Any]]:
    """返回 MDP 键的补全项"""
    items = []
    for key in sorted(_MDP_DOCS):
        first_line = _MDP_DOCS[key].split("\n")[0]
        items.append({
            "label": key,
            "detail": first_line,
            "kind": 6,  # CompletionItemKind.Property
        })
    return items
```

支持的 MDP 键：
- `integrator`
- `nsteps`
- `dt`
- `tcoupl`
- `pcoupl`
- 等等...

### 拓扑部分补全 / Topology Section Completion

```python
def topology_completions() -> list[dict[str, Any]]:
    """返回拓扑部分标题的补全项"""
    items = []
    for name in sorted(_TOPOLOGY_DOCS):
        items.append({
            "label": name,
            "detail": _TOPOLOGY_DOCS[name],
            "kind": 7,  # CompletionItemKind.Class
        })
    return items
```

支持的部分：
- `defaults`
- `atomtypes`
- `moleculetype`
- `atoms`
- `bonds`
- `angles`
- `dihedrals`
- 等等...

## 悬停文档 / Hover Documentation

### MDP 悬停 / MDP Hover

```python
def mdp_hover(key: str) -> Optional[str]:
    """返回键的悬停文档（不区分大小写）"""
    return _MDP_DOCS.get(key.lower())
```

示例：
```
integrator: Integration method. Values: md, steep, cg, l-bfgs, ...
dt: Time step for integration (ps). Type: float.
tcoupl: Temperature coupling method. Values: no, berendsen, ...
```

### 拓扑悬停 / Topology Hover

```python
def topology_hover(section_name: str) -> Optional[str]:
    """返回拓扑部分的悬停文档"""
    return _TOPOLOGY_DOCS.get(section_name.lower())
```

示例：
```
atoms: Atom entries: nr, type, resnr, residue, atom, cgnr, charge, mass.
bonds: Bonded interactions: i, j [funct [parameters]].
```

## 诊断功能 / Diagnostic Features

### MDP 值验证 / MDP Value Validation

```python
def get_valid_mdp_values(key: str) -> Optional[set[str]]:
    """返回 MDP 键的有效值集合"""
    return _MDP_VALID_VALUES.get(key.lower())
```

验证的键：
- `integrator`: {md, steep, cg, l-bfgs, md-vv, ...}
- `cutoff-scheme`: {verlet, group}
- `coulombtype`: {PME, PME-Switch, Ewald, ...}
- `constraints`: {none, all-bonds, h-bonds, all-angles}
- `tcoupl`: {no, berendsen, nose-hoover, ...}
- `pcoupl`: {no, berendsen, parrinello-rahman, ...}

## CLI 命令 / CLI Commands

```bash
# 启动 LSP
gromacs-lsp --stdio

# 诊断
gromacs-lint ./case --json

# 格式化
gromacs-fmt -w md.mdp

# 静态测试
gromacs-test static ./case --json
```

## 配置 / Configuration

### VS Code

```json
{
  "languages": [{
    "id": "gromacs-topology",
    "extensions": [".top", ".itp"],
    "configuration": "gromacs-lsp"
  }],
  "languages": [{
    "id": "gromacs-mdp",
    "extensions": [".mdp"],
    "configuration": "gromacs-lsp"
  }]
}
```

## 路线图 / Roadmap

- [ ] 完整 `.mdp` 解析器支持
- [ ] `.gro` 格式诊断
- [ ] OpenQC 集成
- [ ] 黄金夹具测试
- [ ] 格式化工具完善

## 参考资料 / References

- LSP 实现: `/raw/assets/gromacs_lsp/`
- 补全: `/raw/assets/gromacs_lsp/completion.py`
- 悬停: `/raw/assets/gromacs_lsp/hover.py`
