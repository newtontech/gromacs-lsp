# LLM Wiki 变更日志 / Changelog

## 2026-06-12

### 初始创建 / Initial Creation

创建 gromacs-lsp 项目的 LLM Wiki 知识库，包含：

#### 实体页面 (Entity Pages)
- [x] gromacs-intro.md - GROMACS 简介
- [x] topology-file.md - 拓扑文件格式
- [x] mdp-file.md - MDP 参数文件
- [x] force-field.md - 力场详解
- [x] coordinate-file.md - 坐标文件格式
- [x] bonded-interactions.md - 键合相互作用
- [x] nonbonded-interactions.md - 非键合相互作用
- [x] position-restraints.md - 位置限制
- [x] qmmm-simulation.md - QMMM 模拟
- [x] trajectory-files.md - 轨迹文件格式
- [x] energy-file.md - 能量文件格式

#### 概念页面 (Concept Pages)
- [x] periodic-boundary-conditions.md - 周期性边界条件
- [x] energy-minimization.md - 能量最小化
- [x] equilibration.md - 平衡模拟
- [x] constraints-algorithms.md - 约束算法
- [x] thermostats.md - 恒温器
- [x] barostats.md - 恒压器
- [x] pm-electrostatics.md - PME 静电学
- [x] pull-code.md - Pull 代码
- [x] free-energy-calculations.md - 自由能计算
- [x] membrane-simulations.md - 膜模拟

#### 综合页面 (Synthesis Pages)
- [x] parser-api.md - 拓扑解析器 API
- [x] lsp-features.md - LSP 功能详解
- [x] typical-workflow.md - 典型模拟工作流
- [x] index-files.md - 索引文件参考
- [x] tools-reference.md - GROMACS 工具参考

#### 基础文件
- [x] index.md - 知识库导航
- [x] log.md - 变更日志
- [x] LLM-WIKI-PLAN.md - Wiki 结构计划

#### 资源文件
- [x] raw/assets/ - 源代码和文档副本
- [x] raw/assets/test/ - 测试用例
- [x] raw/assets/gromacs_lsp/ - LSP 实现
- [x] raw/assets/mdparser/ - 解析器实现

### 统计 / Statistics

- **总文件数**: 30+
- **实体页面**: 11
- **概念页面**: 10
- **综合页面**: 5
- **语言**: 双语 (中文/English)

### 覆盖范围 / Coverage

- GROMACS 核心概念 (拓扑、坐标、MDP)
- 力场与相互作用 (键合、非键合)
- 模拟技术 (最小化、平衡、生产)
- 高级主题 (QMMM、自由能、膜模拟)
- LSP 功能与 API

---

## 2026-06-12 (Update 2)

### 文档扩展 / Documentation Expansion

从 GROMACS 官方手册 (manual.gromacs.org) 收集并整合了全面文档。

#### 新增原始资料 / New Raw Assets

- [x] `raw/assets/gromacs-mdp-complete-reference.md` - MDP 完整参数参考 (200+ 参数)
- [x] `raw/assets/gromacs-analysis-tools.md` - 100+ 分析工具完整列表
- [x] `raw/assets/gromacs-remd.md` - 副本交换分子动力学详细参考
- [x] `raw/assets/gromacs-topology-file-formats.md` - 拓扑文件格式完整参考 (含所有函数类型)
- [x] `raw/assets/gromacs-free-energy.md` - 自由能计算方法参考 (TI, BAR, MBAR, soft-core)

#### 新增 Wiki 页面 / New Wiki Pages

概念页面 (Concept Pages):
- [x] replica-exchange.md - 副本交换分子动力学 (T-REMD, H-REMD, Gibbs REMD)
- [x] enhanced-sampling.md - 增强采样技术总览 (AWH, umbrella, metadynamics, simulated tempering)
- [x] multiple-time-stepping.md - 多时间步长 (MTS) 和质量重分配

实体页面 (Entity Pages):
- [x] neural-network-potentials.md - 神经网络势 NNP/MM 混合模拟

综合页面 (Synthesis Pages):
- [x] analysis-tools-reference.md - 分析工具分类参考

#### 更新页面 / Updated Pages

- [x] index.md - 添加新页面链接和参考资料部分

### 更新统计 / Updated Statistics

- **总文件数**: 40+
- **原始资料**: 5 新增
- **新增 Wiki 页面**: 6
- **语言**: 双语 (中文/English)

### 关键发现 / Key Findings

1. GROMACS 2026.2 MDP 包含 200+ 参数选项，覆盖 20+ 功能区域
2. 拓扑文件支持 10+ 键函数类型、10+ 角函数类型、11+ 二面角函数类型
3. REMD 支持 4 种变体：温度交换、哈密顿量交换、联合交换、Gibbs 采样
4. GROMACS 2026 新增 NNP/MM 接口支持神经网络势
5. AWH 自适应偏置方法已成为 GROMACS 内置的增强采样标准工具

---

## 2026-06-13 - Closeout Pass (Issue #27)

### Upstream Coverage Gap Fill
- [x] `raw/assets/upstream-gromacs-reference.md` — Concise manifest of official GROMACS documentation (manual sections, file formats, algorithms, tutorials, force fields)
- [x] `raw/assets/example-em-steep.mdp` — Complete energy minimization MDP (steepest descent, adapted from GROMACS tutorial)
- [x] `raw/assets/example-npt-equil.mdp` — Complete NPT equilibration MDP (V-rescale + Parrinello-Rahman)

### Cross-Reference Verification
- All wiki pages linked from index.md
- index.md updated with new entries and openqc-agent-context.md link

### LSP-Facing Surface Update
- [x] `lsp-capabilities.json` sourceProvenance expanded from 1 to 6 entries (spec, tutorial, manifest)
- [x] `wiki/synthesis/openqc-agent-context.md` enriched with capability table, provenance links, and example input references

### Tooling
- [x] `scripts/wiki-lint.sh` — Lightweight wiki lint (orphan + broken-link check)

---

此日志遵循 Karpathy LLM Wiki 模式。
