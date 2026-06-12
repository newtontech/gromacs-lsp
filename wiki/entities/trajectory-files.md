# 轨迹文件 / Trajectory Files

## 概述 / Overview

GROMACS 使用多种轨迹文件格式来存储模拟过程中原子坐标和速度随时间的变化。

## 轨迹格式 / Trajectory Formats

### XTC (压缩轨迹) / XTC (Compressed Trajectory)

**扩展名**: `.xtc`

**特点**:
- 压缩格式，文件小
- 单精度浮点数
- 丢失精度约 0.001 nm
- 最常用的格式

**创建**:
```bash
gmx mdrun -deffnm md -xtc
```

### TRR (完整轨迹) / TRR (Full Trajectory)

**扩展名**: `.trr`

**特点**:
- 未压缩，完整精度
- 包含坐标、速度、力
- 文件较大
- 用于重启

**创建**:
```bash
gmx mdrun -deffnm md
# 输出 md.trr
```

### TNG (轨迹新世代) / TNG (Trajectory New Generation)

**扩展名**: `.tng`

**特点**:
- 新格式，更灵活
- 支持多帧写入
- 并行 I/O 友好
- 可以存储额外数据

**创建**:
```bash
gmx mdrun -deffnm md -tng
```

## MDP 输出控制 / MDP Output Control

### 坐标输出 / Coordinate Output

```mdp
nstxout = 5000              ; .trr 坐标输出间隔 (0=禁用)
nstxout-compressed = 5000   ; .xtc 坐标输出间隔
```

### 速度输出 / Velocity Output

```mdp
nstvout = 0                ; .trr 速度输出间隔 (0=禁用)
```

### 力输出 / Force Output

```mdp
nstfout = 0                ; .trr 力输出间隔 (0=禁用)
```

## 轨迹处理 / Trajectory Processing

### 提取部分轨迹 / Extract Part of Trajectory

```bash
gmx trjconv -s md.tpr -f md.xtc -o part.xtc \
    -b 10000 -e 20000
# -b: 开始时间 (ps)
# -e: 结束时间 (ps)
```

### 降采样轨迹 / Downsample Trajectory

```bash
gmx trjconv -s md.tpr -f md.xtc -o downsampled.xtc \
    -skip 10
# 每 10 帧取 1 帧
```

### 周期性处理 / Periodicity Handling

```bash
# 去除跳变
gmx trjconv -s md.tpr -f md.xtc -o nojump.xtc \
    -pbc nojump

# 使分子完整
gmx trjconv -s md.tpr -f md.xtc -o whole.xtc \
    -pbc mol -center

# 原子聚类
gmx trjconv -s md.tpr -f md.xtc -o cluster.xtc \
    -pbc cluster -cluster
```

## 格式转换 / Format Conversion

### XTC ↔ TRR

```bash
gmx trjconv -f md.xtc -o md.trr -s md.tpr
gmx trjconv -f md.trr -o md.xtc -s md.tpr
```

### 轨迹 → PDB

```bash
gmx trjconv -f md.xtc -o frame.pdb -s md.tpr \
    -dump 5000
# -dump: 提取特定时间点
```

### 轨迹 → GRO

```bash
gmx trjconv -f md.xtc -o frame.gro -s md.tpr \
    -b 10000 -e 10000
```

## 精度考虑 / Precision Considerations

| 格式 | 精度 | 文件大小 | 用途 |
|------|------|----------|------|
| XTC | ~0.001 nm | 小 | 长期存储 |
| TRR | 完整 | 大 | 重启、分析 |
| TNG | 可配置 | 中等 | 现代 HPC |

## 性能考虑 / Performance Considerations

### I/O 优化 / I/O Optimization

```mdp
nstxout-compressed = 5000   ; 不要太频繁
compressed = yes            ; 压缩
```

### 并行 I/O / Parallel I/O

```bash
gmx mdrun -deffnm md -ntomp 1 -np 4
# 使用 MPI 并行 I/O
```

## 检查轨迹 / Checking Trajectory

```bash
# 查看轨迹信息
gmx check -f md.xtc

# 查看帧数
gmx dump -s md.tpr -f md.xtc | grep "frame"
```

## 参考资料 / References

- GROMACS 轨迹文件: https://manual.gromacs.org/current/reference-manual/file-formats.html
