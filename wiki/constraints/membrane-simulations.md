# 膜模拟 / Membrane Simulations

## 概述 / Overview

膜分子动力学模拟用于研究脂质双层、膜蛋白和细胞膜的结构与功能。

## 膜系统准备 / Membrane System Preparation

### 1. 使用 CHARMM-GUI / Using CHARMM-GUI

1. 访问 CHARMM-GUI (http://charmm-gui.org)
2. 选择 "Membrane Builder"
3. 定义脂质组成和蛋白质
4. 下载 GROMACS 文件

### 2. 使用 insane.py / Using insane.py

```bash
insane.py -o membrane.gro -p topol.top \
    -l POPC:128 -u POPC:12 -x 10 -y 10 -z 15 \
    -T 310 -dh 0.0 -p topol_pure.top \
    -salt 0.15
```

### 3. 手动组装 / Manual Assembly

```bash
# 创建脂质双层
gmx insert-molecules -f box.gro -ci lipid.gro \
    -nmol 128 -o bilayer.gro

# 插入蛋白质
gmx insert-molecules -f bilayer.gro -ci protein.gro \
    -nmol 1 -o complex.gro -p topol.top
```

## 膜特征 / Membrane Characteristics

### 脂质类型 / Lipid Types

| 脂质 | 首尾 | 描述 |
|------|------|------|
| POPC | 16:0-18:1 | 棕榈酰-油酰-磷脂酰胆碱 |
| DPPC | 16:0-16:0 | 二棕榈酰-磷脂酰胆碱 |
| POPE | 16:0-18:1 | 棕榈酰-油酰-磷脂酰乙醇胺 |
| POPS | 16:0-18:1 | 棕榈酰-油酰-磷脂酰丝氨酸 |
| cholesterol | - | 胆固醇 |

### 膜厚度 / Membrane Thickness

```bash
gmx density -s md.tpr -f md.xtc -o density.xvg
# 分析脂质密度分布
```

## MDP 设置 / MDP Settings

### 压力耦合 / Pressure Coupling

```mdp
pcoupl = Parrinello-Rahman
pcoupltype = semiisotropic       ; 半各向同性
tau_p = 5.0                      ; 较长的耦合时间
ref_p = 1.0 1.0                  ; XY 和 Z 方向
compressibility = 4.5e-5 4.5e-5
```

### 温度耦合 / Temperature Coupling

```mdp
tcoupl = V-rescale
tc-grps = Lipid Protein Water_and_ions
tau_t = 1.0 1.0 1.0
ref_t = 310 310 310
```

### 周期性边界条件 / Periodic Boundary Conditions

```mdp
pbc = xyz
```

通常使用 XY 周期性。

## 平衡策略 / Equilibration Strategy

### 1. 脂质平衡 / Lipid Equilibration

```mdp
; 固定蛋白质
define = -DPOSRES

; 弱压力耦合
pcoupl = Berendsen
tau_p = 5.0
```

### 2. 系统平衡 / System Equilibration

```mdp
; 逐步释放位置限制
pcoupl = Parrinello-Rahman
```

## 分析工具 / Analysis Tools

### 1. 脂质有序度 / Lipid Order

```bash
gmx order -s md.tpr -f md.xtc -n lipid.ndx \
    -d z -o order.xvg
```

### 2. 膜厚度 / Membrane Thickness

```bash
gmx density -s md.tpr -f md.xtc -o density.xvg
# 分析脂质磷酸基团分布
```

### 3. 面积每脂质 / Area Per Lipid

```bash
gmx energy -f md.edr -o box.xvg
# 选择 Box-XY
# APL = Box-X × Box-Y / 脂质数
```

### 4. 倾斜角 / Tilt Angle

```bash
gmx bundle -s md.tpr -f md.xtc -o tilt.xvg
```

## 常见问题 / Common Issues

### 1. 脂质翻转 / Lipid Flip-flop

在模拟时间尺度内罕见，但可能发生。

### 2. 盒子变形 / Box Deformation

使用半各向同性压力耦合：
```mdp
pcoupltype = semiisotropic
```

### 3. 水层渗透 / Water Permeation

确保足够的水层：
```bash
gmx editconf -f protein.gro -o boxed.gro -d 1.5
```

## 参考资料 / References

- GROMACS 膜教程: https://manual.gromacs.org/current/user-guide/membrane.html
- CHARMM-GUI: http://charmm-gui.org
- insane.py: https://github.com/patrickfuchs/insane
