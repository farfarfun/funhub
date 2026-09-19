import os
from abc import ABC, abstractmethod
from contextlib import contextmanager

from farlog import getLogger
from fundrive.core import BaseDrive
from fundrive.drives.os import OSDrive

logger = getLogger("funhub")


@contextmanager
def proxy_env(proxies: dict[str, str] | None):
    """在 with 代码块内临时设置 HTTP_PROXY/HTTPS_PROXY 环境变量。

    `funget` 的下载器不接受显式的 `proxies` 参数，但底层 `requests.Session`
    默认会读取环境变量代理设置，因此通过环境变量间接传递代理配置。

    Args:
        proxies: 形如 ``{"http": "...", "https": "..."}`` 的代理配置，为空则不做任何改动

    Yields:
        None
    """
    if not proxies:
        yield
        return

    env_keys = {"http": "HTTP_PROXY", "https": "HTTPS_PROXY"}
    previous = {}
    try:
        for scheme, value in proxies.items():
            env_key = env_keys.get(scheme)
            if not env_key:
                continue
            previous[env_key] = os.environ.get(env_key)
            os.environ[env_key] = value
        yield
    finally:
        for env_key, old_value in previous.items():
            if old_value is None:
                os.environ.pop(env_key, None)
            else:
                os.environ[env_key] = old_value


class SyncResult:
    """同步结果类"""

    def __init__(
        self,
        success: bool,
        fid: str | None = None,
        message: str = "",
        metadata: dict | None = None,
    ):
        """
        初始化同步结果

        Args:
            success: 是否同步成功
            fid: fundrive中的文件ID，用于后续下载
            message: 结果消息
            metadata: 额外的元数据信息
        """
        self.success = success
        self.fid = fid
        self.message = message
        self.metadata = metadata or {}

    def __str__(self):
        return f"SyncResult(success={self.success}, fid={self.fid}, message='{self.message}')"


class BaseProvider(ABC):
    """Git仓库提供者抽象基类

    负责将不同Git平台的仓库同步到fundrive存储中，
    返回fundrive文件ID供后续下载使用
    """

    def __init__(
        self, provider_name: str, drive: BaseDrive = None, root_fid: str = "./"
    ):
        """
        初始化提供者

        Args:
            provider_name: 提供者名称，如 'github', 'huggingface'
            drive: fundrive对象，如果不传则使用OSdrive作为默认值
        """
        self.provider_name = provider_name
        self.logger = getLogger(f"funhub.{provider_name}")
        self.root_fid = root_fid

        # 如果没有传入drive对象，使用OSDrive作为默认值
        if drive is None:
            self.drive = OSDrive()
            self.logger.info("使用OSDrive作为默认存储")
        else:
            self.drive = drive

    @abstractmethod
    def sync_repo_to_drive(
        self, user: str, repo: str, branch: str = "main", force: bool = False
    ) -> SyncResult:
        """
        将仓库同步到fundrive

        Args:
            user: 用户名/组织名
            repo: 仓库名
            branch: 分支名，默认为main
            force: 是否强制重新同步

        Returns:
            SyncResult: 同步结果，包含fid等信息
        """

    @abstractmethod
    def get_repo_info(self, user: str, repo: str) -> dict:
        """
        获取仓库基本信息

        Args:
            user: 用户名/组织名
            repo: 仓库名

        Returns:
            仓库信息字典
        """

    @abstractmethod
    def parse_url(self, url: str) -> tuple[str, str]:
        """
        解析仓库URL，提取用户名和仓库名

        Args:
            url: 仓库URL

        Returns:
            (用户名, 仓库名) 元组
        """

    def get_drive_path(self, user: str, repo: str, branch: str = "main") -> str:
        """
        获取在fundrive中的存储路径

        Args:
            user: 用户名
            repo: 仓库名
            branch: 分支名

        Returns:
            fundrive中的路径
        """
        return f"{self.provider_name}/{user}/{repo}/{branch}"

    def validate_repo_name(self, user: str, repo: str) -> bool:
        """
        验证仓库名称是否有效

        Args:
            user: 用户名
            repo: 仓库名

        Returns:
            是否有效
        """
        if not user or not repo:
            return False

        # 基本的名称验证
        invalid_chars = ["<", ">", ":", '"', "|", "?", "*"]
        for char in invalid_chars:
            if char in user or char in repo:
                return False

        return True

    def upload_to_drive(self, file_path: str, drive_path: str, *args, **kwargs) -> str:
        """
        上传文件到fundrive

        Args:
            file_path: 本地文件路径
            drive_path: fundrive中的路径

        Returns:
            文件ID，失败返回空字符串
        """
        self.logger.info(f"上传文件到fundrive: {file_path} -> {drive_path}")

        # 使用fundrive上传文件
        fid = self.drive.upload_dir(*args, filedir=file_path, fid=drive_path, **kwargs)

        if fid:
            self.logger.success(f"文件上传成功，fid: {fid}")
            return fid
        else:
            self.logger.error("文件上传失败，未获得fid")
            return ""
