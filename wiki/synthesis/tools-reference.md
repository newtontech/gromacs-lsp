# GROMACS 工具参考 / GROMACS Tools Reference

## 概述 / Overview

GROMACS 提供了丰富的命令行工具用于模拟前处理、运行和分析。

## 核心工具分类 / Core Tool Categories

### 1. 前处理工具 / Preprocessing Tools

#### pdb2gmx - 拓扑生成 / Topology Generation

```bash
gmx pdb2gmx -f protein.pdb -o processed.gro \
    -p topol.top -water tip3p -ff amber99sb-ildn
```

选项：
- `-f`: 输入 PDB
- `-o`: 输出 GRO
- `-p`: 输出拓扑
- `-water`: 水模型 (tip3p, tip4p, spce, 等)
- `-ff`: 力场

#### editconf - 结构编辑 / Structure Editing

```bash
gmx editconf -f protein.gro -o boxed.gro \
    -c -d 1.0 -bt cubic
```

选项：
- `-c`: 居中分子
- `-d`: 与盒子边缘距离
- `-bt`: 盒子类型 (cubic, dodecahedron, octahedron)

#### solvate - 溶剂化 / Solvation

```bash
gmx solvate -cp boxed.gro -cs spc216.gro \
    -o solvated.gro -p topol.top
```

#### genion - 离子添加 / Ion Addition

```bash
gmx genion -s ions.tpr -p topol.top -o solv_ions.gro \
    -pname NA -nname CL -neutral -conc 0.15
```

### 2. 处理工具 / Processing Tools

#### grompp - 预处理 / Preprocessing

```bash
gmx grompp -f md.mdp -c npt.gro -p topol.top \
    -o md.tpr -t npt.cpt -r npt.gro
```

选项：
- `-f`: MDP 文件
- `-c`: 坐标文件
- `-p`: 拓扑文件
- `-o`: 输出 TPR
- `-t`: 检查点文件
- `-r`: 参考坐标 (用于位置限制)

#### mdrun - 模拟运行 / Simulation Run

```bash
gmx mdrun -deffnm md -ntomp 4 -nb gpu -pme gpu
```

选项：
- `-deffnm`: 文件名前缀
- `-ntomp`: OpenMP 线程数
- `-nb`: 非键合交互处理
- `-pme`: PME 处理位置
- `-gpuhi`: GPU 隐藏式屏障

### 3. 分析工具 / Analysis Tools

#### energy - 能量分析 / Energy Analysis

```bash
gmx energy -f md.edr -o temperature.xvg
```

#### rms - RMSD 分析 / RMSD Analysis

```bash
gmx rms -s md.tpr -f md.xtc -o rmsd.xvg
```

#### rmsf - RMSF 分析 / RMSF Analysis

```bash
gmx rmsf -s md.tpr -f md.xtc -o rmsf.xvg
```

#### gyrate - 回转半径 / Radius of Gyration

```bash
gmx gyrate -s md.tpr -f md.xtc -o rg.xvg
```

#### sasa - 溶剂可及表面积 / SASA

```bash
gmx sasa -s md.tpr -f md.xtc -o sasa.xvg
```

#### hbond - 氢键分析 / Hydrogen Bond Analysis

```bash
gmx hbond -s md.tpr -f md.xtc -num hb.xvg
```

#### distance - 距离分析 / Distance Analysis

```bash
gmx distance -s md.tpr -f md.xtc -oav dist.xvg \
    -select 'group "Protein" plus group "Ligand"'
```

#### angle - 角度分析 / Angle Analysis

```bash
gmx angle -s md.tpr -f md.xtc -o angle.xvg \
    -type dihedral -n dihedral.ndx
```

### 4. 轨迹工具 / Trajectory Tools

#### trjconv - 轨迹转换 / Trajectory Conversion

```bash
gmx trjconv -s md.tpr -f md.xtc -o processed.xtc \
    -pbc nojump -center
```

选项：
- `-pbc nojump`: 去除跳变
- `-pbc mol`: 使分子完整
- `-center`: 居中分子
- `-ur compact`: 紧凑表示

#### trjcat - 轨迹连接 / Trajectory Concatenation

```bash
gmx trjcat -f part1.xtc part2.xtc -o combined.xtc
```

#### check - 检查工具 / Check Tool

```bash
gmx check -f md.xtc
```

### 5. 索引工具 / Index Tools

#### make_ndx - 创建索引 / Create Index

```bash
gmx make_ndx -f md.gro -o index.ndx
```

#### select - 高级选择 / Advanced Selection

```bash
gmx select -s md.tpr -select 'resname LIG' -on ligand.ndx
```

### 6. 特殊工具 / Special Tools

#### mindist - 最小距离 / Minimum Distance

```bash
gmx mindist -s md.tpr -f md.xtc -od mindist.xvg \
    -pi -group "Protein" -group "Ligand"
```

#### clustsize - 聚类大小 / Cluster Size

```bash
gmx clustsize -s md.tpr -f md.xtc -o cluster.xvg
```

#### densmap - 密度图 / Density Map

```bash
gmx densmap -s md.tpr -f md.xtc -o density.xpm
```

## 参考资料 / References

- GROMACS 工具: https://manual.gromacs.org/current/onlinehelp/
- gmx 命令: `gmx [command] -h`
