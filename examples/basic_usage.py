#!/usr/bin/env python3
"""
FunHub 基本使用示例

本示例展示了如何使用FunHub的解耦架构：
1. 同步端：使用FunHub将Git仓库同步到fundrive
2. 使用端：用户直接使用fid通过fundrive下载数据
"""

from funhub import RepoManager, config


def sync_github_repo(repo_manager):
    """同步GitHub仓库示例"""
    print("=== 同步GitHub仓库示例 ===")

    # 同步一个GitHub仓库
    url = "https://github.com/pytorch/pytorch"
    print(f"正在同步仓库: {url}")

    result = repo_manager.sync_repo(url, branch="main")

    if result.success:
        print(f"✅ 同步成功!")
        print(f"📁 文件ID (fid): {result.fid}")
        print(f"💡 使用提示: 请使用此fid通过fundrive下载数据")
        print(f"   示例命令: fundrive download {result.fid} ./pytorch")
        return result.fid
    else:
        print(f"❌ 同步失败: {result.message}")
        return None


def sync_huggingface_model():
    """同步HuggingFace模型示例"""
    print("\n=== 同步HuggingFace模型示例 ===")

    # 同步一个HuggingFace模型
    url = "https://huggingface.co/bert-base-uncased"
    print(f"正在同步模型: {url}")

    result = repo_manager.sync_repo(url)

    if result.success:
        print(f"✅ 同步成功!")
        print(f"📁 文件ID (fid): {result.fid}")
        print(f"💡 使用提示: 请使用此fid通过fundrive下载模型")
        print(f"   示例命令: fundrive download {result.fid} ./bert-base-uncased")
        return result.fid
    else:
        print(f"❌ 同步失败: {result.message}")
        return None


def list_synced_repos():
    """列出已同步的仓库"""
    print("\n=== 已同步的仓库列表 ===")

    repos = repo_manager.list_synced_repos()

    if not repos:
        print("📭 没有找到已同步的仓库")
        return

    print(f"📋 找到 {len(repos)} 个已同步的仓库:")

    for repo in repos:
        source = repo.get("source", "unknown")
        user = repo.get("user", "unknown")
        repo_name = repo.get("repo", "unknown")
        branch = repo.get("branch", "main")
        fid = repo.get("fid", "unknown")

        print(f"\n📁 {source}/{user}/{repo_name} (分支: {branch})")
        print(f"   文件ID: {fid}")
        print(f"   URL: {repo.get('url', 'unknown')}")
        print(f"   💡 下载命令: fundrive download {fid} ./{repo_name}")


def get_repo_info():
    """获取仓库信息示例"""
    print("\n=== 获取仓库信息示例 ===")

    # 获取GitHub仓库信息
    source = "github"
    user = "pytorch"
    repo = "pytorch"

    fid = repo_manager.get_repo_fid(source, user, repo)

    if fid:
        print(f"📋 仓库: {source}/{user}/{repo}")
        print(f"📁 文件ID: {fid}")

        # 获取详细信息
        info = repo_manager.get_repo_info(source, user, repo)
        if info:
            print(f"📝 描述: {info.get('description', 'N/A')}")
            print(f"⭐ Stars: {info.get('stars', 0)}")
            print(f"🍴 Forks: {info.get('forks', 0)}")
            print(f"💻 语言: {info.get('language', 'N/A')}")

        print(f"💡 下载命令: fundrive download {fid} ./{repo}")
    else:
        print(f"❌ 仓库 {source}/{user}/{repo} 尚未同步")


def configure_proxy():
    """配置代理示例"""
    print("\n=== 配置代理示例 ===")

    # 设置HTTP代理（如果需要）
    # config.set("network.proxy.http", "http://proxy.example.com:8080")
    # config.set("network.proxy.https", "https://proxy.example.com:8080")

    # 设置网络超时
    config.set("network.timeout", 60)

    # 保存配置
    config.save_config()

    print("⚙️ 配置已更新")
    print(f"🌐 网络超时: {config.get('network.timeout')}秒")
    print(f"🔧 配置文件: {config.config_path}")


def demonstrate_decoupled_workflow():
    """演示完整的解耦工作流程"""
    print("\n" + "=" * 50)
    print("🏗️  FunHub 解耦架构演示")
    print("=" * 50)

    print("\n🎯 架构说明:")
    print("┌─────────────────┐    sync     ┌─────────────────┐")
    print("│                 │ ──────────> │                 │")
    print("│     FunHub      │             │    FunDrive     │")
    print("│   (同步端)       │   返回 fid   │   (存储端)       │")
    print("│                 │ <────────── │                 │")
    print("└─────────────────┘             └─────────────────┘")
    print("                                          │")
    print("                                          │ download")
    print("                                          ▼")
    print("                                 ┌─────────────────┐")
    print("                                 │                 │")
    print("                                 │   用户端         │")
    print("                                 │  (使用端)        │")
    print("                                 │                 │")
    print("                                 └─────────────────┘")

    print("\n📋 工作流程:")
    print("1. 🔄 同步阶段: FunHub从Git平台下载仓库，上传到fundrive，返回fid")
    print("2. 📥 使用阶段: 用户直接使用fid通过fundrive下载数据")
    print("3. 🎯 完全解耦: 同步和使用完全分离，互不依赖")


def main():
    """主函数"""
    print("🚀 FunHub 使用示例")

    # 演示解耦架构
    demonstrate_decoupled_workflow()

    # 配置代理（如果需要）
    configure_proxy()

    # 同步GitHub仓库
    github_fid = sync_github_repo()

    # 同步HuggingFace模型
    hf_fid = sync_huggingface_model()

    # 列出已同步的仓库
    list_synced_repos()

    # 获取仓库信息
    get_repo_info()

    print("\n" + "=" * 50)
    print("✅ 示例完成!")
    print("💡 重要提醒:")
    print("   - FunHub只负责同步，不负责下载")
    print("   - 请使用返回的fid通过fundrive下载数据")
    print("   - 这样实现了完全的解耦架构")
    print("=" * 50)


if __name__ == "__main__":
    main()
