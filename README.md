# FunHub

FunHub 是一个专门用于将 GitHub、HuggingFace 等 Git 仓库同步到 fundrive 的工具。

## 🎯 设计理念

FunHub 采用**完全解耦**的架构设计：

- **同步端**：FunHub 只负责将 Git 仓库同步到 fundrive，并返回文件 ID (fid)
- **使用端**：用户直接使用 fid 通过 fundrive 下载数据，无需再经过 FunHub

这种设计实现了数据同步与数据使用的完全分离，提高了系统的灵活性和可维护性。

## 🚀 快速开始

### 安装

```bash
pip install funhub
```

### 基本使用

1. **同步仓库到 fundrive**
```bash
# 同步 GitHub 仓库
funhub sync https://github.com/user/repo

# 同步 HuggingFace 仓库
funhub sync https://huggingface.co/user/model

# 指定分支
funhub sync https://github.com/user/repo --branch dev
```

2. **查看已同步的仓库**
```bash
# 列出所有已同步的仓库
funhub list

# 只显示 GitHub 仓库
funhub list --source github
```

3. **获取仓库信息和 fid**
```bash
funhub info github user repo
```

4. **使用 fid 下载数据**
```bash
# 注意：下载由 fundrive 负责，不经过 funhub
fundrive download <fid> ./target_folder
```

## 📋 功能特性

- ✅ 支持 GitHub 仓库同步
- ✅ 支持 HuggingFace 仓库同步  
- ✅ 支持指定分支同步
- ✅ 同步记录管理
- ✅ 代理支持
- ✅ 配置管理
- ✅ 完全解耦的架构设计

## 🏗️ 架构说明

```
┌─────────────────┐    sync     ┌─────────────────┐
│                 │ ──────────> │                 │
│     FunHub      │             │    FunDrive     │
│   (同步端)       │   返回 fid   │   (存储端)       │
│                 │ <────────── │                 │
└─────────────────┘             └─────────────────┘
                                          │
                                          │ download
                                          ▼
                                 ┌─────────────────┐
                                 │                 │
                                 │   用户端         │
                                 │  (使用端)        │
                                 │                 │
                                 └─────────────────┘
```

### 工作流程

1. **同步阶段**：FunHub 从 Git 平台下载仓库，上传到 fundrive，返回 fid
2. **使用阶段**：用户直接使用 fid 通过 fundrive 下载数据
3. **完全解耦**：同步和使用完全分离，互不依赖

## 🛠️ 开发指南

### 环境搭建

```bash
# 克隆项目
git clone https://github.com/farfarfun/funhub.git
cd funhub

# 安装依赖
pip install -e .
```

### 代码规范

- 使用中文注释
- 遵循 PEP8 编码规范
- 函数和类必须有文档字符串
- 重要的业务逻辑必须有注释说明

### 测试

```bash
# 运行测试
pytest tests/

# 测试覆盖率
pytest --cov=funhub tests/
```

## 📖 API 文档

详细的 API 文档请参考 [docs/API.md](docs/API.md)

## 📝 变更日志

详细的变更记录请参考 [docs/CHANGELOG.md](docs/CHANGELOG.md)

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 🐳 推荐

如果你在寻找 AI 模型路由服务,欢迎通过我的推荐链接体验 [OrcaRouter](https://www.orcarouter.ai/ref/ref_99e484f735afe381b366)。

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 📞 联系方式

- 项目地址：https://github.com/farfarfun/funhub
- 问题反馈：https://github.com/farfarfun/funhub/issues