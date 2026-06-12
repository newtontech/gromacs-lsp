# 力场 / Force Field

## 概述 / Overview

力场 (Force Field) 是分子动力学模拟的核心，定义了原子间的相互作用能。GROMACS 支持多种力场，每种力场都包含一组参数文件。

## 常用力场 / Common Force Fields

### AMBER 力场

```top
#include "amber99.ff/forcefield.itp"
#include "amber99.ff/amber99sb.ldn"
```

### CHARMM 力场

```top
#include "charmm36-mar2019.ff/forcefield.itp"
```

### OPLS 力场

```top
#include "oplsaa.ff/forcefield.itp"
```

### GROMOS 力场

```top
#include "gromos54a7.ff/forcefield.itp"
```

## 力场组成 / Force Field Components

### 1. 原子类型 / Atom Types

定义不同元素的化学环境：

```top
[ atomtypes ]
; name  bond.type  at.num  mass   charge   ptype  sigma    epsilon
CT     CT         6       12.011  0.0     A      0.337    0.4184
HC     HC         1       1.008   0.0     A      0.235    0.065
```

### 2. 键参数 / Bond Parameters

```top
[ bondtypes ]
; ai   aj   funct   b0      kb
CT    CT   1       0.153   334720
```

### 3. 角参数 / Angle Parameters

```top
[ angletypes ]
; ai   aj   ak   funct   th0     cth
HC    CT   HC   1       109.5   460.24
```

### 4. 二面角参数 / Dihedral Parameters

```top
[ dihedraltypes ]
; ai   aj   ak   al   funct   phi0    fc
CT    CT   CT   CT   9       0.0     0.0
```

### 5. 非键合参数 / Non-bonded Parameters

```top
[ nonbond_params ]
; ai   aj   funct   sigma   epsilon
CT    CT    1       0.337   0.4184
```

## 力场文件结构 / Force Field File Structure

```text
forcefield.ff/
├── forcefield.itp       ; 主包含文件
├── atomtype.atp          ; 原子类型
├── ffnonbonded.itp       ; 非键合参数
├── ffbonded.itp          ; 键合参数
└── *.itp                 ; 残基特定文件
```

## [defaults] 部分 / Defaults Section

定义非键合相互作用的默认处理方式：

```top
[ defaults ]
; nbfunc   comb-rule  gen-pairs  fudgeLJ  fudgeQQ
1          2          yes        0.5      0.8333
```

参数说明：
- `nbfunc`: Lennard-Jones 函数 (1=Van der Waals, 2=Buckingham)
- `comb-rule`: 组合规则 (1=Lorentz-Berthelot, 2=几何平均)
- `gen-pairs`: 是否生成 1-4 对
- `fudgeLJ`: 1-4 LJ 衰减因子
- `fudgeQQ`: 1-4 电荷衰减因子

## 节水模型 / Water Models

### TIP3P

```top
#include "amber99.ff/tip3p.itp"
```

### TIP4P

```top
#include "amber99.ff/tip4p.itp"
```

### SPC/E

```top
#include "amber99.ff/spce.itp"
```

## 力场选择 / Force Field Selection

选择力场时考虑：

1. **分子类型**: 蛋白质 (AMBER/CHARMM), 核酸 (AMBER/CHARMM), 脂质 (CHARMM36)
2. **目标性质**: 结构, 热力学, 动力学
3. **兼容性**: 与其他工具的兼容性
4. **文献支持**: 验证和引用

## 参考资料 / References

- AMBER 力场: http://ambermd.org/
- CHARMM 力场: https://www.charmm.org/
- GROMACS 力场: https://manual.gromacs.org/current/reference-manual/topologies/force-field.html
