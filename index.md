# GROMACS LSP Wiki 导航 / Navigation

## 概述 / Overview

这是 gromacs-lsp 项目的知识库，包含 GROMACS 分子动力学模拟的完整参考。

## 目录结构 / Structure

```
wiki/
├── entities/       # 实体页面 (GROMACS 特定概念)
├── concepts/       # 概念页面 (跨领域思想)
└── synthesis/      # 综合页面 (API 参考、工作流)
```

## 核心主题 / Core Topics

### 基础 / Basics

- [GROMACS 简介](wiki/entities/gromacs-intro.md) - GROMACS 概述和特点
- [拓扑文件](wiki/entities/topology-file.md) - .top/.itp 文件格式
- [MDP 文件](wiki/entities/mdp-file.md) - 模拟参数文件
- [坐标文件](wiki/entities/coordinate-file.md) - .gro 文件格式

### 力场与相互作用 / Force Fields & Interactions

- [力场](wiki/entities/force-field.md) - 力场类型和参数
- [键合相互作用](wiki/entities/bonded-interactions.md) - 键、角、二面角
- [非键合相互作用](wiki/entities/nonbonded-interactions.md) - LJ 和库仑相互作用
- [PME 静电学](wiki/concepts/pm-electrostatics.md) - 长程静电处理

### 模拟技术 / Simulation Techniques

- [能量最小化](wiki/concepts/energy-minimization.md) - 结构优化
- [平衡模拟](wiki/concepts/equilibration.md) - NVT/NPT 平衡
- [恒温器](wiki/concepts/thermostats.md) - 温度控制
- [恒压器](wiki/concepts/barostats.md) - 压力控制
- [周期性边界条件](wiki/concepts/periodic-boundary-conditions.md) - PBC 设置

### 高级主题 / Advanced Topics

- [位置限制](wiki/entities/position-restraints.md) - 原子位置约束
- [约束算法](wiki/constraints/constraints-algorithms.md) - LINCS/SHAKE
- [QMMM 模拟](wiki/entities/qmmm-simulation.md) - 量子/分子力学混合
- [Pull 代码](wiki/constraints/pull-code.md) - 外力施加
- [自由能计算](wiki/constraints/free-energy-calculations.md) - 热力学积分
- [膜模拟](wiki/constraints/membrane-simulations.md) - 膜蛋白系统
- [副本交换 / REMD](wiki/concepts/replica-exchange.md) - 增强采样方法
- [增强采样技术](wiki/concepts/enhanced-sampling.md) - AWH, 伞状采样, metadynamics
- [多时间步长 / MTS](wiki/concepts/multiple-time-stepping.md) - 性能优化
- [神经网络势 / NNP](wiki/entities/neural-network-potentials.md) - NNP/MM 混合模拟

### 文件格式 / File Formats

- [轨迹文件](wiki/entities/trajectory-files.md) - .xtc/.trr/.tng
- [能量文件](wiki/entities/energy-file.md) - .edr 格式
- [索引文件](wiki/synthesis/index-files.md) - .ndx 原子组

### API 与工具 / API & Tools

- [解析器 API](wiki/synthesis/parser-api.md) - 拓扑解析器接口
- [LSP 功能](wiki/synthesis/lsp-features.md) - 语言服务器功能
- [OpenQC 智能体上下文](wiki/synthesis/openqc-agent-context.md) - Agent-facing LSP capability surface and source provenance
- [工具参考](wiki/synthesis/tools-reference.md) - GROMACS 命令行工具
- [典型工作流](wiki/synthesis/typical-workflow.md) - 完整模拟流程
- [分析工具参考](wiki/synthesis/analysis-tools-reference.md) - 100+ 分析工具详解

### 完整参考资料 / Complete Reference Sources

- [MDP 完整参数参考](raw/assets/gromacs-mdp-complete-reference.md) - 所有 MDP 选项
- [拓扑文件格式参考](raw/assets/gromacs-topology-file-formats.md) - 完整拓扑格式
- [分析工具参考](raw/assets/gromacs-analysis-tools.md) - 全部分析工具列表
- [自由能计算](raw/assets/gromacs-free-energy.md) - TI, BAR, MBAR 方法
- [REMD 参考](raw/assets/gromacs-remd.md) - 副本交换方法
- [上游参考链接](raw/assets/upstream-gromacs-reference.md) - Official GROMACS documentation link manifest
- [示例: 能量最小化 MDP](raw/assets/example-em-steep.mdp) - Steepest descent minimization template
- [示例: NPT 平衡 MDP](raw/assets/example-npt-equil.mdp) - V-rescale + Parrinello-Rahman template

## 快速链接 / Quick Links

- [源代码](raw/assets/) - 原始源文件
- [LSP 实现](raw/assets/gromacs_lsp/) - 语言服务器代码
- [解析器实现](raw/assets/mdparser/) - 拓扑解析器代码
- [测试文件](raw/assets/test/) - 测试用例

## 贡献 / Contributing

欢迎贡献！请参考项目根目录的 `CONTRIBUTING.md`。

## 许可证 / License

本项目基于 MIT 许可证。

---

最后更新: 2026-06-12 (第二次更新)
