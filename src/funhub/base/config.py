"""
配置管理模块
用于管理funhub的配置信息，包括存储路径、代理设置等
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from funutil import getLogger

logger = getLogger("funhub")


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径，默认为 ~/.funhub/config.yaml
        """
        if config_path is None:
            self.config_dir = Path.home() / ".funhub"
            self.config_path = self.config_dir / "config.yaml"
        else:
            self.config_path = Path(config_path)
            self.config_dir = self.config_path.parent

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f) or {}
                logger.info(f"已加载配置文件: {self.config_path}")
                return config
            except Exception as e:
                logger.error(f"加载配置文件失败: {e}")
                return self._get_default_config()
        else:
            logger.info("配置文件不存在，使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "storage": {
                "base_path": str(Path.home() / "fundrive"),
                "github_path": "github",
                "huggingface_path": "huggingface",
                "gitee_path": "gitee",
            },
            "network": {
                "timeout": 30,
                "retry_times": 3,
                "proxy": {"http": None, "https": None},
            },
            "download": {"chunk_size": 8192, "max_workers": 4, "skip_existing": True},
        }

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(
                    self._config,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    indent=2,
                )
            logger.success(f"配置已保存到: {self.config_path}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点分隔的嵌套键，如 'storage.base_path'
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split(".")
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        """
        keys = key.split(".")
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value
        logger.info(f"设置配置 {key} = {value}")

    def get_storage_path(self, source: str, user: str, repo: str) -> Path:
        """
        获取仓库存储路径

        Args:
            source: 来源，如 'github', 'huggingface'
            user: 用户名
            repo: 仓库名

        Returns:
            存储路径
        """
        base_path = Path(self.get("storage.base_path"))
        source_path = self.get(f"storage.{source}_path", source)

        return base_path / source_path / user / repo

    @property
    def base_storage_path(self) -> Path:
        """获取基础存储路径"""
        return Path(self.get("storage.base_path"))


# 全局配置实例
base_config = Config()
