"""
FunHub - 将GitHub、HuggingFace等Git仓库同步到fundrive的工具

FunHub采用完全解耦的架构设计：
- 同步端：FunHub只负责将Git仓库同步到fundrive，并返回文件ID(fid)
- 使用端：用户直接使用fid通过fundrive下载数据，无需再经过FunHub

这种设计实现了数据同步与数据使用的完全分离，提高了系统的灵活性和可维护性。
"""

__author__ = "FarFarFun Team"
__email__ = "contact@farfarfun.com"

# 导入核心组件
from .manager import RepoManager
from .base import base_config, BaseProvider, SyncResult

# 导入具体提供者
from .providers.github import GitHubProvider
from .providers.huggingface import HuggingFaceProvider

# 创建默认的仓库管理器实例
repo_manager = RepoManager()

__all__ = [
    "RepoManager",
    "repo_manager",
    "base_config",
    "BaseProvider",
    "SyncResult",
    "GitHubProvider",
    "HuggingFaceProvider",
]
