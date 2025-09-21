# 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.0] - 2025-01-21

### 新增
- 🎉 初始版本发布
- ✨ 支持GitHub仓库同步到fundrive
- ✨ 支持HuggingFace仓库同步到fundrive
- ✨ 完全解耦的架构设计
- ✨ 命令行接口(CLI)支持
- ✨ 配置管理功能
- ✨ 同步记录管理
- ✨ 代理支持
- ✨ 多分支同步支持

### 架构特性
- 🏗️ **解耦设计**：同步端(funhub)与使用端(fundrive)完全分离
- 🔄 **同步端职责**：只负责将Git仓库同步到fundrive，返回fid
- 📥 **使用端职责**：用户直接使用fid通过fundrive下载数据
- 🎯 **单一职责**：每个组件专注于自己的核心功能

### CLI命令
- `funhub sync <url>` - 同步Git仓库到fundrive
- `funhub list` - 列出已同步的仓库
- `funhub info <source> <user> <repo>` - 显示仓库信息和fid
- `funhub remove <source> <user> <repo>` - 删除同步记录
- `funhub config show` - 显示当前配置
- `funhub config set <key> <value>` - 设置配置项

### 支持的平台
- GitHub (github.com)
- HuggingFace (huggingface.co)

### 技术实现
- 基于Python 3.12+
- 使用Click构建CLI
- 支持YAML配置文件
- 异步下载和上传
- 完整的错误处理和日志记录

### 文档
- 📖 完整的README.md说明文档
- 📋 详细的API文档
- 🏗️ 架构设计说明
- 💡 使用示例和最佳实践

## [未来计划]

### 即将发布 (v0.2.0)
- [ ] 支持Gitee仓库同步
- [ ] 支持GitLab仓库同步
- [ ] 增量同步功能
- [ ] 批量同步支持
- [ ] Web界面管理

### 长期规划 (v1.0.0)
- [ ] 分布式同步支持
- [ ] 同步任务调度
- [ ] 监控和告警
- [ ] 插件系统
- [ ] 企业级功能

## 贡献者

感谢所有为本项目做出贡献的开发者！

---

## 版本说明

### 版本号格式
本项目使用语义化版本号：`主版本号.次版本号.修订号`

- **主版本号**：不兼容的API修改
- **次版本号**：向下兼容的功能性新增
- **修订号**：向下兼容的问题修正

### 变更类型
- `新增` - 新功能
- `变更` - 对现有功能的变更
- `废弃` - 即将移除的功能
- `移除` - 已移除的功能
- `修复` - 问题修复
- `安全` - 安全相关的修复
