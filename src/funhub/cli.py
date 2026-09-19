"""
命令行接口模块
提供funhub的命令行操作功能
"""

from importlib.metadata import version

import click
from farlog import getLogger

from funhub.base import base_config

from .manager import repo_manager

logger = getLogger("funhub.cli")


@click.group()
@click.version_option(version=version("funhub"))
def main():
    """FunHub - 将GitHub、HuggingFace等Git仓库同步到fundrive的工具

    注意：funhub只负责同步Git仓库到fundrive并返回fid，
    使用时请直接通过fundrive和fid下载数据，实现完全解耦。
    """


@main.command()
@click.argument("url")
@click.option("--force", "-f", is_flag=True, help="强制重新同步，即使仓库已存在")
@click.option("--branch", "-b", default="main", help="指定分支名，默认为main")
def sync(url: str, force: bool, branch: str):
    """
    同步Git仓库到fundrive

    URL: 仓库URL，支持GitHub、HuggingFace等平台
    """
    click.echo(f"开始同步仓库到fundrive: {url}")

    result = repo_manager.sync_repo(url, branch=branch, force=force)

    if result.success:
        click.echo(click.style("✓ 同步成功!", fg="green"))
        click.echo(f"文件ID (fid): {result.fid}")
        click.echo(f"消息: {result.message}")
    else:
        click.echo(click.style("✗ 同步失败!", fg="red"))
        click.echo(f"错误: {result.message}")
        exit(1)


@main.command()
@click.option("--source", "-s", help="指定来源 (github, huggingface等)")
def list(source: str | None):
    """列出已同步的仓库"""
    repos = repo_manager.list_synced_repos(source)

    if not repos:
        click.echo("没有找到已同步的仓库")
        return

    click.echo(f"找到 {len(repos)} 个已同步的仓库:")
    click.echo()

    for repo in repos:
        source_name = repo.get("source", "unknown")
        user = repo.get("user", "unknown")
        repo_name = repo.get("repo", "unknown")
        branch = repo.get("branch", "main")
        fid = repo.get("fid", "unknown")

        click.echo(f"📁 {source_name}/{user}/{repo_name} (分支: {branch})")
        click.echo(f"   文件ID: {fid}")
        click.echo(f"   URL: {repo.get('url', 'unknown')}")
        click.echo(f"   同步时间: {repo.get('sync_time', 'unknown')}")
        click.echo()


@main.command()
@click.argument("source")
@click.argument("user")
@click.argument("repo")
@click.option("--branch", "-b", default="main", help="指定分支名，默认为main")
def remove(source: str, user: str, repo: str, branch: str):
    """
    删除同步记录

    SOURCE: 来源 (github, huggingface等)
    USER: 用户名
    REPO: 仓库名
    """
    click.confirm(
        f"确定要删除同步记录 {source}/{user}/{repo} (分支: {branch}) 吗？", abort=True
    )

    success = repo_manager.remove_sync_record(source, user, repo, branch)

    if success:
        click.echo(click.style("✓ 删除成功!", fg="green"))
    else:
        click.echo(click.style("✗ 删除失败!", fg="red"))
        exit(1)


@main.command()
@click.argument("source")
@click.argument("user")
@click.argument("repo")
@click.option("--branch", "-b", default="main", help="指定分支名，默认为main")
def info(source: str, user: str, repo: str, branch: str):
    """
    显示仓库信息

    SOURCE: 来源 (github, huggingface等)
    USER: 用户名
    REPO: 仓库名
    """
    fid = repo_manager.get_repo_fid(source, user, repo, branch)

    if not fid:
        click.echo(
            click.style(
                f"仓库未同步: {source}/{user}/{repo} (分支: {branch})", fg="red"
            )
        )
        exit(1)

    click.echo(f"仓库信息: {source}/{user}/{repo} (分支: {branch})")
    click.echo(f"文件ID (fid): {fid}")
    click.echo()
    click.echo(click.style("💡 使用提示:", fg="cyan"))
    click.echo("   请使用此fid通过fundrive直接下载仓库数据")
    click.echo(f"   示例: fundrive download {fid} ./target_folder")
    click.echo()

    # 获取在线仓库信息
    repo_info = repo_manager.get_repo_info(source, user, repo)
    if repo_info:
        click.echo("📋 仓库详情:")
        click.echo(f"   名称: {repo_info.get('name', 'unknown')}")
        click.echo(f"   描述: {repo_info.get('description', 'N/A')}")
        if "language" in repo_info:
            click.echo(f"   主要语言: {repo_info.get('language', 'N/A')}")
        if "stars" in repo_info:
            click.echo(f"   Stars: {repo_info.get('stars', 0)}")


@main.group()
def config_cmd():
    """配置管理"""


@config_cmd.command(name="show")
def show_config():
    """显示当前配置"""
    click.echo("当前配置:")
    click.echo(f"存储路径: {base_config.get('storage.base_path')}")
    click.echo(f"GitHub路径: {base_config.get('storage.github_path')}")
    click.echo(f"HuggingFace路径: {base_config.get('storage.huggingface_path')}")
    click.echo(f"网络超时: {base_config.get('network.timeout')}秒")
    click.echo(f"重试次数: {base_config.get('network.retry_times')}")
    click.echo(f"跳过已存在: {base_config.get('download.skip_existing')}")


@config_cmd.command(name="set")
@click.argument("key")
@click.argument("value")
def set_config(key: str, value: str):
    """
    设置配置项

    KEY: 配置键，如 storage.base_path
    VALUE: 配置值
    """
    # 尝试转换布尔值和数字
    if value.lower() in ("true", "false"):
        value = value.lower() == "true"
    elif value.isdigit():
        value = int(value)

    base_config.set(key, value)
    base_config.save_config()

    click.echo(click.style(f"✓ 配置已更新: {key} = {value}", fg="green"))


@config_cmd.command(name="init")
def init_config():
    """初始化配置文件"""
    base_config.save_config()
    click.echo(
        click.style(f"✓ 配置文件已初始化: {base_config.config_path}", fg="green")
    )


if __name__ == "__main__":
    main()
