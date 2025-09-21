"""
仓库管理器模块
负责管理Git仓库的同步到fundrive和从fundrive下载
"""

import json
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from funutil import getLogger

from funhub.base import BaseProvider, SyncResult

logger = getLogger("funhub")


class RepoManager:
    """仓库管理器

    负责协调不同提供者将Git仓库同步到fundrive，
    并管理从fundrive下载仓库的功能
    """

    def __init__(self, drive=None):
        """初始化仓库管理器

        Args:
            drive: fundrive对象，如果不传则各个提供者会使用OSdrive作为默认值
        """
        self.drive = drive
        self.providers: Dict[str, BaseProvider] = {}
        self.sync_records: Dict[str, Dict] = {}
        self._register_providers()
        self._load_sync_records()

    def _register_providers(self):
        """注册所有可用的仓库提供者"""
        try:
            from .providers.github import GitHubProvider
            from .providers.huggingface import HuggingFaceProvider

            self.providers["github"] = GitHubProvider(self.drive)
            self.providers["huggingface"] = HuggingFaceProvider(self.drive)

            logger.info(
                f"已注册 {len(self.providers)} 个仓库提供者: {list(self.providers.keys())}"
            )
        except ImportError as e:
            logger.error(f"注册提供者时发生导入错误: {e}")

    def _load_sync_records(self):
        """加载同步记录"""
        try:
            records_file = config.config_dir / "sync_records.json"
            if records_file.exists():
                with open(records_file, "r", encoding="utf-8") as f:
                    self.sync_records = json.load(f)
                logger.info(f"已加载 {len(self.sync_records)} 条同步记录")
            else:
                self.sync_records = {}
                logger.info("同步记录文件不存在，使用空记录")
        except Exception as e:
            logger.error(f"加载同步记录失败: {e}")
            self.sync_records = {}

    def _save_sync_records(self):
        """保存同步记录"""
        try:
            records_file = config.config_dir / "sync_records.json"
            with open(records_file, "w", encoding="utf-8") as f:
                json.dump(self.sync_records, f, ensure_ascii=False, indent=2)
            logger.info("同步记录已保存")
        except Exception as e:
            logger.error(f"保存同步记录失败: {e}")

    def sync_repo(
        self, url: str, branch: str = "main", force: bool = False
    ) -> SyncResult:
        """
        同步Git仓库到fundrive

        Args:
            url: 仓库URL
            branch: 分支名
            force: 是否强制重新同步

        Returns:
            SyncResult: 同步结果
        """
        try:
            # 识别仓库来源
            source = self._identify_source(url)
            if not source:
                return SyncResult(False, message=f"无法识别仓库来源: {url}")

            if source not in self.providers:
                return SyncResult(False, message=f"不支持的仓库来源: {source}")

            provider = self.providers[source]

            # 解析URL获取用户名和仓库名
            try:
                user, repo = provider.parse_url(url)
            except Exception as e:
                return SyncResult(False, message=f"解析URL失败: {e}")

            # 验证仓库名称
            if not provider.validate_repo_name(user, repo):
                return SyncResult(False, message=f"无效的仓库名称: {user}/{repo}")

            # 生成记录键
            record_key = f"{source}/{user}/{repo}/{branch}"

            # 检查是否已同步且不强制更新
            if not force and record_key in self.sync_records:
                existing_record = self.sync_records[record_key]
                fid = existing_record.get("fid")
                if fid:
                    logger.info(f"仓库已同步，返回已有fid: {fid}")
                    return SyncResult(
                        True,
                        fid=fid,
                        message="仓库已存在于fundrive中",
                        metadata=existing_record,
                    )

            # 执行同步
            logger.info(f"开始同步仓库: {source}/{user}/{repo} (分支: {branch})")
            sync_result = provider.sync_repo_to_drive(user, repo, branch, force)

            # 保存同步记录
            if sync_result.success and sync_result.fid:
                self.sync_records[record_key] = {
                    "source": source,
                    "user": user,
                    "repo": repo,
                    "branch": branch,
                    "url": url,
                    "fid": sync_result.fid,
                    "sync_time": str(Path().cwd()),  # 简化时间戳
                    "metadata": sync_result.metadata,
                }
                self._save_sync_records()
                logger.success(f"仓库同步成功: {record_key}, fid: {sync_result.fid}")
            else:
                logger.error(f"仓库同步失败: {sync_result.message}")

            return sync_result

        except Exception as e:
            logger.error(f"同步仓库时发生错误: {e}")
            return SyncResult(False, message=f"同步过程中发生错误: {e}")

    def _identify_source(self, url: str) -> Optional[str]:
        """
        识别仓库来源

        Args:
            url: 仓库URL

        Returns:
            来源名称
        """
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()

            if "github.com" in domain:
                return "github"
            elif "huggingface.co" in domain:
                return "huggingface"
            elif "gitee.com" in domain:
                return "gitee"

            return None
        except Exception:
            return None

    def get_repo_fid(
        self, source: str, user: str, repo: str, branch: str = "main"
    ) -> Optional[str]:
        """
        获取仓库在fundrive中的文件ID

        Args:
            source: 来源
            user: 用户名
            repo: 仓库名
            branch: 分支名

        Returns:
            文件ID，如果不存在返回None
        """
        record_key = f"{source}/{user}/{repo}/{branch}"
        record = self.sync_records.get(record_key)
        return record.get("fid") if record else None

    def list_synced_repos(self, source: Optional[str] = None) -> List[Dict]:
        """
        列出已同步的仓库

        Args:
            source: 指定来源，None表示所有来源

        Returns:
            同步记录列表
        """
        repos = []
        for record_key, record in self.sync_records.items():
            if source and record.get("source") != source:
                continue
            repos.append(record)

        return repos

    def remove_sync_record(
        self, source: str, user: str, repo: str, branch: str = "main"
    ) -> bool:
        """
        删除同步记录

        Args:
            source: 来源
            user: 用户名
            repo: 仓库名
            branch: 分支名

        Returns:
            是否删除成功
        """
        record_key = f"{source}/{user}/{repo}/{branch}"
        if record_key in self.sync_records:
            del self.sync_records[record_key]
            self._save_sync_records()
            logger.info(f"已删除同步记录: {record_key}")
            return True
        else:
            logger.warning(f"同步记录不存在: {record_key}")
            return False

    def get_repo_info(self, source: str, user: str, repo: str) -> Dict:
        """
        获取仓库信息

        Args:
            source: 来源
            user: 用户名
            repo: 仓库名

        Returns:
            仓库信息字典
        """
        if source not in self.providers:
            return {}

        provider = self.providers[source]
        return provider.get_repo_info(user, repo)


# 全局仓库管理器实例
repo_manager = RepoManager()
