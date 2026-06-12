# GROMACS 简介 / GROMACS Introduction

## 概述 / Overview

GROMACS (Groningen Machine for Chemicals Simulations) 是一个用于分子动力学模拟的软件包，主要用于模拟生物分子（如蛋白质、脂质、核酸）在溶液中的行为。

## 核心特点 / Core Features

- **高性能**：优化的算法和并行计算支持
- **多精度**：支持单精度和双精度计算
- **多平台**：Linux、Windows、macOS
- **开源**：GPLv2 许可证

## 文件格式 / File Formats

GROMACS 使用多种文件格式：

| 格式 | 用途 |
|------|------|
| `.top` | 拓扑文件 - 定义分子拓扑结构和力场参数 |
| `.itp` | 包含文件 - 可重用的分子定义 |
| `.gro` | 坐标文件 - 原子坐标和速度 |
| `.mdp` | 模拟参数文件 - 控制模拟设置 |
| `.xtc` | 压缩轨迹文件 |
| `.trr` | 完整轨迹文件 |

## 模拟工作流 / Simulation Workflow

```
结构准备 → 拓扑生成 → 能量最小化 → 平衡 → 生产模拟 → 分析
```

## LSP 支持 / LSP Support

gromacs-lsp 为以下文件提供语言服务器支持：

- `.top` / `.itp` - 拓扑文件解析和补全
- `.mdp` - 模拟参数补全和验证
- `.gro` - 坐标文件解析

## 参考资料 / References

- GROMACS 官方文档: https://manual.gromacs.org/
- 源代码: `/raw/assets/mdparser/` - 拓扑解析器实现
- LSP 实现: `/raw/assets/gromacs_lsp/` - 语言服务器代码
