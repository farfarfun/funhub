"""
GitHub仓库提供者
实现GitHub仓库同步到fundrive的功能
"""

import os
import requests
import tempfile
from typing import Dict, Tuple
from urllib.parse import urlparse

from funhub.base import BaseProvider, SyncResult
from funhub.base import base_config


class GitHubProvider(BaseProvider):
    """GitHub仓库提供者"""

    def __init__(self, drive=None):
        """初始化GitHub提供者"""
        super().__init__("github", drive)
        self.api_base = "https://api.github.com"
        self.download_base = "https://github.com"

    def sync_repo_to_drive(
        self, user: str, repo: str, branch: str = "main", force: bool = False
    ) -> SyncResult:
        """
        将GitHub仓库同步到fundrive

        Args:
            user: GitHub用户名
            repo: 仓库名
            branch: 分支名
            force: 是否强制重新同步

        Returns:
            SyncResult: 同步结果
        """
        try:
            # 构建下载URL
            download_url = (
                f"{self.download_base}/{user}/{repo}/archive/refs/heads/{branch}.zip"
            )

            # 设置请求参数
            timeout = base_config.get("network.timeout", 30)
            proxies = self._get_proxies()

            self.logger.info(f"开始下载GitHub仓库: {download_url}")

            # 下载ZIP文件到临时目录
            with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as temp_file:
                response = requests.get(
                    download_url, timeout=timeout, proxies=proxies, stream=True
                )
                response.raise_for_status()

                # 写入临时文件
                for chunk in response.iter_content(
                    chunk_size=base_config.get("download.chunk_size", 8192)
                ):
                    if chunk:
                        temp_file.write(chunk)

                temp_zip_path = temp_file.name

            self.logger.info("下载完成，准备上传到fundrive")

            # 上传到fundrive
            drive_path = self.get_drive_path(user, repo, branch)
            fid = self.upload_to_drive(temp_zip_path, drive_path)

            # 清理临时文件
            os.unlink(temp_zip_path)

            if fid:
                self.logger.success(f"GitHub仓库同步成功: {user}/{repo}, fid: {fid}")

                # 获取仓库信息作为元数据
                repo_info = self.get_repo_info(user, repo)

                return SyncResult(
                    success=True,
                    fid=fid,
                    message=f"成功同步到fundrive: {drive_path}",
                    metadata={
                        "drive_path": drive_path,
                        "repo_info": repo_info,
                        "file_size": os.path.getsize(temp_zip_path)
                        if os.path.exists(temp_zip_path)
                        else 0,
                    },
                )
            else:
                return SyncResult(False, message="上传到fundrive失败")

        except requests.exceptions.RequestException as e:
            self.logger.error(f"网络请求失败: {e}")
            return SyncResult(False, message=f"网络请求失败: {e}")
        except Exception as e:
            self.logger.error(f"同步GitHub仓库时发生错误: {e}")
            return SyncResult(False, message=f"同步过程中发生错误: {e}")

    def get_repo_info(self, user: str, repo: str) -> Dict:
        """
        获取GitHub仓库信息

        Args:
            user: GitHub用户名
            repo: 仓库名

        Returns:
            仓库信息字典
        """
        try:
            api_url = f"{self.api_base}/repos/{user}/{repo}"
            timeout = base_config.get("network.timeout", 30)
            proxies = self._get_proxies()

            response = requests.get(api_url, timeout=timeout, proxies=proxies)
            response.raise_for_status()

            data = response.json()

            return {
                "name": data.get("name"),
                "full_name": data.get("full_name"),
                "description": data.get("description"),
                "language": data.get("language"),
                "stars": data.get("stargazers_count"),
                "forks": data.get("forks_count"),
                "size": data.get("size"),
                "default_branch": data.get("default_branch"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "clone_url": data.get("clone_url"),
                "html_url": data.get("html_url"),
            }

        except requests.exceptions.RequestException as e:
            self.logger.error(f"获取GitHub仓库信息失败: {e}")
            return {}
        except Exception as e:
            self.logger.error(f"解析GitHub仓库信息时发生错误: {e}")
            return {}

    def parse_url(self, url: str) -> Tuple[str, str]:
        """
        解析GitHub仓库URL

        Args:
            url: GitHub仓库URL

        Returns:
            (用户名, 仓库名) 元组
        """
        try:
            parsed = urlparse(url)
            path_parts = parsed.path.strip("/").split("/")

            if len(path_parts) >= 2:
                user = path_parts[0]
                repo = path_parts[1]
                # 移除.git后缀
                if repo.endswith(".git"):
                    repo = repo[:-4]
                return user, repo
            else:
                raise ValueError(f"无效的GitHub URL格式: {url}")

        except Exception as e:
            self.logger.error(f"解析GitHub URL失败: {e}")
            raise

    def _get_proxies(self) -> Dict:
        """获取代理设置"""
        http_proxy = base_config.get("network.proxy.http")
        https_proxy = base_config.get("network.proxy.https")

        proxies = {}
        if http_proxy:
            proxies["http"] = http_proxy
        if https_proxy:
            proxies["https"] = https_proxy

        return proxies
