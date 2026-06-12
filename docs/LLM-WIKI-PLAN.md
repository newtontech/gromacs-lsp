# GROMACS LSP Wiki 结构计划 / Wiki Structure Plan

## 概述 / Overview

本文档描述了 gromacs-lsp 项目的 LLM Wiki 知识库结构，采用 Karpathy LLM Wiki 模式。

## 目录结构 / Directory Structure

```
gromacs-lsp/
├── raw/
│   └── assets/
│       ├── test/              # 测试文件
│       │   ├── test_parse_topologies/
│       │   └── test_tasks/
│       ├── gromacs_lsp/       # LSP 实现
│       │   ├── completion.py
│       │   ├── diagnostics.py
│       │   ├── hover.py
│       │   └── ...
│       ├── mdparser/          # 拓扑解析器
│       │   ├── topology.py
│       │   ├── _gmx_nodes.py
│       │   └── ...
│       ├── README.md
│       ├── README.newtontech.md
│       ├── CONTRIBUTING.md
│       └── pyproject.toml
├── wiki/
│   ├── entities/              # GROMACS 特定实体
│   │   ├── gromacs-intro.md
│   │   ├── topology-file.md
│   │   ├── mdp-file.md
│   │   ├── force-field.md
│   │   ├── coordinate-file.md
│   │   ├── bonded-interactions.md
│   │   ├── nonbonded-interactions.md
│   │   ├── position-restraints.md
│   │   ├── qmmm-simulation.md
│   │   ├── trajectory-files.md
│   │   └── energy-file.md
│   ├── concepts/              # 跨领域概念
│   │   ├── periodic-boundary-conditions.md
│   │   ├── energy-minimization.md
│   │   ├── equilibration.md
│   │   ├── constraints-algorithms.md
│   │   ├── thermostats.md
│   │   ├── barostats.md
│   │   ├── pm-electrostatics.md
│   │   ├── pull-code.md
│   │   ├── free-energy-calculations.md
│   │   └── membrane-simulations.md
│   └── synthesis/             # API 参考和工作流
│       ├── parser-api.md
│       ├── lsp-features.md
│       ├── typical-workflow.md
│       ├── index-files.md
│       └── tools-reference.md
├── index.md                   # 导航中心
├── log.md                     # 变更日志
└── docs/
    └── LLM-WIKI-PLAN.md      # 本文件
```

## Wiki 内容分类 / Wiki Content Categories

### 1. 实体页面 (11 页)

GROMACS 特定的实体和概念：

| 文件 | 主题 | 关键内容 |
|------|------|----------|
| gromacs-intro.md | GROMACS 简介 | 特点、文件格式、工作流 |
| topology-file.md | 拓扑文件 | .top/.itp 格式、结构、解析 |
| mdp-file.md | MDP 文件 | 模拟参数、验证、场景配置 |
| force-field.md | 力场 | AMBER/CHARMM/OPLS、参数 |
| coordinate-file.md | 坐标文件 | .gro 格式、转换、盒子类型 |
| bonded-interactions.md | 键合相互作用 | 键、角、二面角、约束 |
| nonbonded-interactions.md | 非键合相互作用 | LJ、库仑、PME、截断 |
| position-restraints.md | 位置限制 | POSRES、应用场景、力常数 |
| qmmm-simulation.md | QMMM 模拟 | 量子/分子力学混合 |
| trajectory-files.md | 轨迹文件 | .xtc/.trr/.tng 格式、处理 |
| energy-file.md | 能量文件 | .edr 格式、提取项、分析 |

### 2. 概念页面 (10 页)

跨领域概念和思想：

| 文件 | 主题 | 关键内容 |
|------|------|----------|
| periodic-boundary-conditions.md | PBC | 盒子类型、处理、最小镜像约定 |
| energy-minimization.md | 能量最小化 | 算法、收敛标准、策略 |
| equilibration.md | 平衡模拟 | NVT/NPT、监控、收敛标准 |
| constraints-algorithms.md | 约束算法 | LINCS、SHAKE、SETTLE |
| thermostats.md | 恒温器 | Berendsen、V-rescale、Nose-Hoover |
| barostats.md | 恒压器 | Berendsen、Parrinello-Rahman、MTTK |
| pm-electrostatics.md | PME | 粒子网格 Ewald、参数、优化 |
| pull-code.md | Pull 代码 | 伞状采样、恒力、SMD |
| free-energy-calculations.md | 自由能计算 | TI、FEP、BAR、工作流 |
| membrane-simulations.md | 膜模拟 | 膜准备、平衡、分析 |

### 3. 综合页面 (5 页)

API 参考、工作流和工具：

| 文件 | 主题 | 关键内容 |
|------|------|----------|
| parser-api.md | 解析器 API | GromacsTopologyParser、节点类型 |
| lsp-features.md | LSP 功能 | 补全、诊断、悬停 |
| typical-workflow.md | 典型工作流 | 完整模拟流程 |
| index-files.md | 索引文件 | .ndx 格式、make_ndx、select |
| tools-reference.md | 工具参考 | GROMACS 命令行工具 |

## 命名规范 / Naming Conventions

- **文件名**: 小写 kebab-case (`topology-file.md`)
- **标题**: 双语 (中文/English)
- **章节**: 使用 ## 标题
- **代码**: 使用代码块和语法高亮

## 内容风格 / Content Style

- **双语格式**: 中文标题，英文术语
- **表格**: 使用 Markdown 表格总结信息
- **代码示例**: 可执行的命令和配置
- **交叉引用**: 链接到相关页面
- **参考资料**: 每页底部提供参考链接

## 维护指南 / Maintenance Guidelines

### 添加新内容

1. 确定内容类型 (entity/concept/synthesis)
2. 创建相应文件
3. 更新 `index.md` 导航
4. 在 `log.md` 记录变更

### 更新现有内容

1. 编辑相应文件
2. 在 `log.md` 添加变更记录
3. 保持双语格式

### 从源代码提取

当更新源代码时：
1. 检查 API 变化
2. 更新相关 synthesis 页面
3. 更新代码示例

## 未来扩展 / Future Extensions

### 计划添加

- [ ] 窗函数分析
- [ ] 相关函数分析
- [ ] 伞状采样详细教程
- [ ] 束缚态计算
- [ ] 粗粒化力场
- [ ] 共聚焦显微镜模拟

### 计划增强

- [ ] 更多代码示例
- [ ] 可视化图表
- [ ] 常见问题解答
- [ ] 故障排除指南

## 参考资料 / References

- 原始源代码: `raw/assets/`
- GROMACS 官方文档: https://manual.gromacs.org/
- MDParser 源码: https://github.com/janjoswig/MDParser

---

文档版本: 1.0
创建日期: 2026-06-12
