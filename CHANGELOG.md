# 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
并且本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.1.3] - 2026-09-19

### 修复
- 修复 `RepoManager._load_sync_records` / `_save_sync_records` 引用未导入的 `config`
  导致每次构造 `RepoManager` 都触发 `NameError` 并被吞掉、同步记录持久化实际从未生效的问题
- 修复 CLI `config show` / `config set` / `config init` 因 `from funhub.base import config`
  实际拿到的是模块对象而非配置单例、调用 `.get()`/`.set()` 必然抛 `AttributeError` 的问题
- 修正 `examples/basic_usage.py`、`examples/fundrive_integration.py` 中不存在的
  `from funhub import config` 导入及 `fundrive.OSdrive`（应为 `OSDrive`）等示例与实际公开 API 不一致的问题
- 修复 `BaseProvider.__init__` 在调用方显式传入 `drive` 对象时未赋值 `self.drive`，
  导致后续 `upload_to_drive` 必然抛 `AttributeError` 的问题
- 修复 `docs/API.md` 中残留的 `Optional`/`Dict`/`Tuple` 旧式类型标注，与源码实际签名不一致的问题

### 变更
- 日志入口由 `funutil.getLogger` 切换为组织自有的 `farlog.getLogger`
- GitHub / HuggingFace 仓库归档下载由直接使用 `requests.get(stream=True)` 切换为组织自有的
  `funget.download`
- 公开 API 的类型标注由 `typing.Optional`/`List`/`Dict`/`Tuple` 旧式写法切换为
  `str | None`、`list[...]`、`dict[...]` 等 3.10+ 新式写法
- `pyproject.toml` 显式声明 `license = "MIT"` 与 `license-files`
- 补充 `.gitignore` 对 `*.db`、`.run/`、`logs/`、`.idea/`、`.vscode/` 的忽略规则
- README 末尾追加组织统一的「关于 farfarfun」区块

### 新增
- 补充 `RepoManager` 同步成功路径、同步记录持久化（跨实例加载）、删除记录成功/失败分支、
  CLI `sync`/`config` 子命令成功与失败退出码等公开 API 的测试覆盖

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

### 支持的平台
- GitHub (github.com)
- HuggingFace (huggingface.co)
