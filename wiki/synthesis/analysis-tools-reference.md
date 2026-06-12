# GROMACS 分析工具参考 / Analysis Tools Reference

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：1

## 核心摘要 / Core Summary

GROMACS 提供 100+ 分析工具，通过 `gmx` 命令统一调用。

## 工具分类 / Tool Categories

### 结构分析 / Structure Analysis

| 工具 | 功能 | 常用选项 |
|------|------|---------|
| `gmx rms` | RMSD 计算 | `-s ref.tpr -f traj.xtc` |
| `gmx rmsf` | RMSF 计算 | `-s topol.tpr -f traj.xtc` |
| `gmx gyrate` | 回转半径 | `-s topol.tpr -f traj.xtc` |
| `gmx sasa` | 溶剂可及表面积 | `-s topol.tpr -f traj.xtc` |
| `gmx distance` | 原子间距离 | `-s topol.tpr -f traj.xtc` |
| `gmx gangle` | 角度和二面角 | `-g1 vector/vector` |

### 轨迹处理 / Trajectory Processing

| 工具 | 功能 |
|------|------|
| `gmx trjconv` | 轨迹转换 (`-pbc nojump`) |
| `gmx trjcat` | 轨迹拼接 |
| `gmx convert-trj` | 格式转换 |

### 能量与热力学 / Energy and Thermodynamics

| 工具 | 功能 |
|------|------|
| `gmx energy` | 提取能量分量 |
| `gmx bar` | BAR 自由能 |
| `gmx wham` | WHAM 伞状采样分析 |
| `gmx awh` | AWH PMF 提取 |
| `gmx sham` | 2D 自由能面 |

### 蛋白质特有 / Protein-specific

| 工具 | 功能 |
|------|------|
| `gmx dssp` | 二级结构 |
| `gmx rama` | Ramachandran 图 |
| `gmx hbond` | 氢键分析 |
| `gmx saltbr` | 盐桥 |
| `gmx cluster` | 构象聚类 |

### 径向分布与有序性 / RDF and Order

| 工具 | 功能 |
|------|------|
| `gmx rdf` | 径向分布函数 |
| `gmx order` | 脂质有序参数 |
| `gmx density` | 密度分布 |

## 典型分析工作流 / Typical Workflow

```bash
# RMSD
echo "Protein" | gmx rms -s md.tpr -f md.xtc -o rmsd.xvg

# RMSF
echo "Protein" | gmx rmsf -s md.tpr -f md.xtc -o rmsf.xvg

# 氢键
echo "Protein" "Protein" | gmx hbond -s md.tpr -f md.xtc -num hbond.xvg

# WHAM
gmx wham -it tpr_files.dat -if pullf_files.dat -o pmf.xvg
```

## 索引组 / Default Groups

System, Protein, Protein-H, C-alpha, Backbone, MainChain, SideChain,
Water, non-Water, Ion, Water_and_Ions, DNA, RNA, Other

## 动态选择 / Dynamic Selections

```
resname LYS and within 3 of group "Protein"
name CA and resid 50 to 100
```

## 来源 / References

- `/raw/assets/gromacs-analysis-tools.md`
- https://manual.gromacs.org/current/user-guide/cmdline.html
