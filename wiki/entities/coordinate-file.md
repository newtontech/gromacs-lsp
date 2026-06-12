# 坐标文件 / Coordinate File (.gro)

## 概述 / Overview

GRO 格式 (`.gro`) 是 GROMACS 的原生坐标文件格式，包含原子坐标、速度和盒子尺寸信息。

## 文件格式 / File Format

```
标题行 (可选)
原子数
坐标列 (每行一个原子)
盒子向量
```

### 示例 / Example

```
GROMACS generated trj file
    24
    1SOL     OW    1   0.300   2.630   2.313  0.0000  0.4167 -0.2512
    1SOL    HW1    2   0.340   2.700   2.217  0.0000  0.8334 -0.5025
    1SOL    HW2    3   0.340   2.630   2.396  0.0000  0.8334 -0.5025
    2SOL     OW    4   0.300   1.075   1.655  0.0000 -0.2085  0.0620
    2SOL    HW1    5   0.336   1.100   1.581  0.0000 -0.4170  0.1240
    2SOL    HW2    6   0.336   1.075   1.727  0.0000 -0.4170  0.1240
    3SOL     OW    7   0.300   3.450   1.320  0.0000  0.0000  0.0000
    ...
   3.32100   3.32100   3.32100
```

## 列格式 / Column Format

每行的列：

| 列 | 位置 | 内容 |
|---|------|------|
| 1 | 1-5 | 残基编号 (右对齐) |
| 2 | 6-10 | 残基名称 |
| 3 | 11-15 | 原子名称 |
| 4 | 16-20 | 原子编号 (右对齐) |
| 5 | 21-28 | X 坐标 (nm) |
| 6 | 29-36 | Y 坐标 (nm) |
| 7 | 37-44 | Z 坐标 (nm) |
| 8 | 45-52 | VX 速度 (nm/ps, 可选) |
| 9 | 53-60 | VY 速度 (nm/ps, 可选) |
| 10 | 61-68 | VZ 速度 (nm/ps, 可选) |

## 盒子向量 / Box Vectors

最后一行包含盒子尺寸：

```
   xx   yy   zz
```

对于三斜盒子：

```
   xx   yy   zz   xy   xz   yz
```

## 单位 / Units

- 坐标: 纳米 (nm)
- 速度: nm/ps = 1000 m/s
- 盒子: nm

## 与其他格式转换 / Conversion

### PDB → GRO

```bash
gmx editconf -f input.pdb -o output.gro
```

### GRO → PDB

```bash
gmx editconf -f input.gro -o output.pdb
```

### 添加盒子 / Add Box

```bash
gmx editconf -f protein.gro -o boxed.gro -c -d 1.0 -bt cubic
```

## 速度信息 / Velocity Information

速度信息仅在以下文件中存在：

- 平衡后的结构 (从 NVT 模拟输出)
- 重新初始化速度后的结构

使用 `gen-vel = yes` 生成速度：

```bash
gmx grompp -f minim.mdp -c struct.gro -p topol.top -o min.tpr
gmx mdrun -deffnm min -v
```

## 中心分子 / Center Molecule

```bash
gmx editconf -f complex.gro -o centered.gro -center
```

## 盒子类型 / Box Types

- `cubic`: 立方盒子
- `dodecahedron`: 十二面体盒子
- `octahedron`: 八面体盒子
- `triclinic`: 三斜盒子

## 参考资料 / References

- GROMACS 坐标文件: https://manual.gromacs.org/current/reference-manual/file-formats.html#gro
