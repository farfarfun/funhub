#!/usr/bin/env python3
"""
FunHub Fundrive集成示例

本示例展示了如何使用真实的fundrive对象与FunHub集成：
1. 使用默认OSdrive
2. 使用自定义fundrive对象
3. 完整的同步和下载工作流程
"""

from funhub import RepoManager, config


def example_with_default_drive():
    """使用默认OSdrive的示例"""
    print("=== 使用默认OSdrive示例 ===")

    # 创建RepoManager，不传drive参数，会自动使用OSdrive
    repo_manager = RepoManager()

    # 同步一个小型GitHub仓库
    url = "https://github.com/octocat/Hello-World"
    print(f"正在同步仓库: {url}")

    result = repo_manager.sync_repo(url, branch="master")

    if result.success:
        print(f"✅ 同步成功!")
        print(f"📁 文件ID (fid): {result.fid}")
        print(f"💡 使用OSdrive存储，数据保存在本地文件系统")
        return result.fid
    else:
        print(f"❌ 同步失败: {result.message}")
        return None


def example_with_custom_drive():
    """使用自定义fundrive对象的示例"""
    print("\n=== 使用自定义fundrive对象示例 ===")

    try:
        # 导入fundrive相关模块
        from fundrive import OSdrive
        # 如果有其他drive类型，也可以使用，比如：
        # from fundrive import S3drive, AliyunOSSdrive

        # 创建自定义drive对象
        custom_drive = OSdrive()

        # 创建RepoManager，传入自定义drive
        repo_manager = RepoManager(drive=custom_drive)

        # 同步一个HuggingFace模型
        url = "https://huggingface.co/microsoft/DialoGPT-small"
        print(f"正在同步模型: {url}")

        result = repo_manager.sync_repo(url)

        if result.success:
            print(f"✅ 同步成功!")
            print(f"📁 文件ID (fid): {result.fid}")
            print(f"💡 使用自定义drive存储")
            return result.fid
        else:
            print(f"❌ 同步失败: {result.message}")
            return None

    except ImportError as e:
        print(f"❌ 导入fundrive失败: {e}")
        print("💡 请确保已安装fundrive: pip install fundrive")
        return None


def demonstrate_download_workflow(fid):
    """演示下载工作流程"""
    if not fid:
        print("\n❌ 没有有效的fid，跳过下载演示")
        return

    print(f"\n=== 下载工作流程演示 ===")
    print(f"📁 文件ID: {fid}")
    print("\n🎯 解耦架构说明:")
    print("1. 同步阶段已完成 - FunHub将仓库上传到fundrive并返回fid")
    print("2. 使用阶段 - 用户直接使用fid通过fundrive下载")
    print("\n💡 下载方式:")
    print("方式1: 使用fundrive命令行工具")
    print(f"   fundrive download {fid} ./downloaded_repo")
    print("\n方式2: 使用fundrive Python API")
    print("   from fundrive import OSdrive")
    print("   drive = OSdrive()")
    print(f"   drive.download('{fid}', './downloaded_repo')")
    print("\n方式3: 使用fundrive Web界面")
    print(f"   访问fundrive管理界面，输入fid: {fid}")


def list_and_manage_repos():
    """列出和管理已同步的仓库"""
    print("\n=== 仓库管理示例 ===")

    # 使用默认RepoManager
    repo_manager = RepoManager()

    # 列出所有已同步的仓库
    repos = repo_manager.list_synced_repos()

    if not repos:
        print("📭 没有找到已同步的仓库")
        return

    print(f"📋 找到 {len(repos)} 个已同步的仓库:")

    for i, repo in enumerate(repos, 1):
        source = repo.get("source", "unknown")
        user = repo.get("user", "unknown")
        repo_name = repo.get("repo", "unknown")
        branch = repo.get("branch", "main")
        fid = repo.get("fid", "unknown")
        sync_time = repo.get("sync_time", "unknown")

        print(f"\n{i}. 📁 {source}/{user}/{repo_name}")
        print(f"   分支: {branch}")
        print(f"   文件ID: {fid}")
        print(f"   同步时间: {sync_time}")
        print(f"   💡 下载: fundrive download {fid} ./{repo_name}")


def configure_fundrive_settings():
    """配置fundrive相关设置"""
    print("\n=== Fundrive配置示例 ===")

    # 配置存储路径
    config.set("storage.base_path", "~/fundrive")

    # 配置网络设置
    config.set("network.timeout", 300)  # 5分钟超时，适合大文件上传
    config.set("network.retry_times", 3)

    # 配置并发设置
    config.set("download.chunk_size", 8192)  # 8KB chunks
    config.set("download.max_workers", 4)

    # 保存配置
    config.save_config()

    print("⚙️ Fundrive配置已更新:")
    print(f"📁 存储路径: {config.get('storage.base_path')}")
    print(f"⏱️ 网络超时: {config.get('network.timeout')}秒")
    print(f"🔄 重试次数: {config.get('network.retry_times')}")
    print(f"📦 块大小: {config.get('download.chunk_size')} bytes")
    print(f"🧵 最大工作线程: {config.get('download.max_workers')}")


def main():
    """主函数"""
    print("🚀 FunHub Fundrive集成示例")
    print("=" * 50)

    # 配置fundrive设置
    configure_fundrive_settings()

    # 示例1: 使用默认OSdrive
    fid1 = example_with_default_drive()

    # 示例2: 使用自定义drive对象
    fid2 = example_with_custom_drive()

    # 演示下载工作流程
    demonstrate_download_workflow(fid1 or fid2)

    # 列出和管理仓库
    list_and_manage_repos()

    print("\n" + "=" * 50)
    print("✅ Fundrive集成示例完成!")
    print("\n🎯 关键要点:")
    print("1. RepoManager可以接受自定义drive对象")
    print("2. 如果不传drive，会自动使用OSdrive")
    print("3. 所有Provider都通过BaseProvider使用真实的fundrive")
    print("4. 同步和下载完全解耦，通过fid连接")
    print("5. 用户可以直接使用fundrive API下载数据")
    print("=" * 50)


if __name__ == "__main__":
    main()
