# 索引文件 / Index Files (.ndx)

## 概述 / Overview

索引文件 (`.ndx`) 用于定义原子组，便于分析和操作特定原子集合。

## 文件格式 / File Format

```ndx
[ Protein ]
; 原子编号
1 2 3 4 5 6 7 8 9 10
11 12 13 14 15

[ Ligand ]
100 101 102 103 104 105

[ SOL ]
200 201 202 203 204 205 206 207 208 209
```

- 组名用 `[` 和 `]` 括起
- 原子编号从 1 开始
- 空行忽略

## 创建索引文件 / Creating Index Files

### 使用 make_ndx / Using make_ndx

```bash
gmx make_ndx -f md.gro -o index.ndx
```

交互式命令：
```
> 0                  ; 显示所有组
> 1 | 2              ; 合并组 1 和 2
> name 20 Protein    ; 重命名组 20
> q                  ; 保存并退出
```

### 常用命令 / Common Commands

| 命令 | 描述 |
|------|------|
| `0` | 显示所有组 |
| `1` | 选择组 1 |
| `1 | 2` | 合并组 1 和 2 |
| `1 & 2` | 组 1 和 2 的交集 |
| `1 ! 2` | 组 1 中不在组 2 的部分 |
| `ri 1 3 5` | 保留 1, 3, 5 |
| `del 1` | 删除组 1 |
| `name 1 NewName` | 重命名组 1 |
| `q` | 保存并退出 |

### 预定义组 / Predefined Groups

GROMACS 自动创建：
- `System`: 所有原子
- `Protein`: 蛋白质原子
- `Protein-H`: 蛋白质氢原子
- `C-alpha`: Cα 原子
- `Backbone`: 骨架原子 (N, CA, C)
- `MainChain`: 主链原子
- `SideChain`: 侧链原子
- `Water`: 水分子
- `SOL`: 溶剂
- `Non-Water`: 非水原子

## 分析工具中的索引 / Index Files in Analysis Tools

### RMSD 计算 / RMSD Calculation

```bash
gmx rms -s md.tpr -f md.xtc -n index.ndx -o rmsd.xvg
```

### 氢键分析 / Hydrogen Bond Analysis

```bash
gmx hbond -s md.tpr -f md.xtc -n index.ndx \
    -num hb.xvg -dist dist.xvg
```

### 距离计算 / Distance Calculation

```bash
gmx distance -s md.tpr -f md.xtc -n index.ndx \
    -select 'group "Protein" plus group "Ligand"' \
    -oav dist.xvg
```

## 典型应用 / Typical Applications

### 1. 定义蛋白质子区域 / Define Protein Sub-regions

```bash
gmx make_ndx -f md.gro
> r 10 20              ; 残基 10-20
> name 0 Helix
> r 30 40
> name 1 Loop
> q
```

### 2. 定义配体环境 / Define Ligand Environment

```bash
gmx make_ndx -f md.gro
> "Protein" | "Ligand"   ; 合并蛋白质和配体
> name 0 Complex
> "Complex" ! "Ligand"   ; 蛋白质
> name 1 Protein_only
> q
```

### 3. 定义溶剂壳层 / Define Solvent Shell

```bash
gmx select -s md.tpr -select 'group "SOL" and distance from group "Protein" < 0.5' -on shell.ndx
```

## 编辑索引文件 / Editing Index Files

### 手动编辑 / Manual Editing

文本编辑器直接编辑 `.ndx` 文件。

### 使用 gmx select / Using gmx select

```bash
gmx select -s md.tpr -select 'resname LIG and atomname CA' -on ligand_ca.ndx
```

## 组合选择 / Selection Combinations

```bash
gmx select -s md.tpr \
    -select 'resname ALA and (atomname N or atomname CA or atomname C)' \
    -on ala_backbone.ndx
```

## 参考资料 / References

- GROMACS 索引文件: https://manual.gromacs.org/current/reference-manual/file-formats.html
- gmx select: https://manual.gromacs.org/current/onlinehelp/gmx-select.html
