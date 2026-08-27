"""轻量冒烟测试 (smoke tests)。

目标：确认 funhub 包能够被正常导入、核心公开类/函数能以简单参数
构造/调用、CLI 入口能正常响应 --help，而不是对业务逻辑做穷尽式覆盖。

注意事项：
- `funhub.base.config.base_config` 是模块级单例，导入 `funhub` 包时会
  立即以 ``Path.home() / ".funhub"`` 作为默认配置目录并在磁盘上创建它。
  为了避免测试污染开发者的真实 HOME 目录，这里在 `import funhub` 之前先
  把 HOME 环境变量重定向到一个临时目录。
- GitHub / HuggingFace provider 中所有实际发起网络请求的方法
  (`sync_repo_to_drive`, `get_repo_info`) 都通过 `unittest.mock` 打桩，
  不会产生真实的网络调用。
- provider 构造时默认会创建 `fundrive.drives.os.OSDrive()`，其 `__init__`
  只是记录一个路径字符串，不会读写磁盘，因此无需额外打桩；但为了保持
  测试的独立性/明确性，涉及 provider 的用例都显式传入 `MagicMock()` 作为
  `drive` 参数。
"""

import os
import shutil
import tempfile

import pytest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# 必须在 `import funhub` 之前重定向 HOME，防止污染开发者真实的 ~/.funhub。
# ---------------------------------------------------------------------------
_FAKE_HOME = tempfile.mkdtemp(prefix="funhub_test_home_")
os.environ["HOME"] = _FAKE_HOME

import funhub  # noqa: E402
from funhub.base.config import Config  # noqa: E402
from funhub.base.provider import BaseProvider, SyncResult  # noqa: E402
from funhub.manager import RepoManager  # noqa: E402
from funhub.providers.github import GitHubProvider  # noqa: E402
from funhub.providers.huggingface import HuggingFaceProvider  # noqa: E402


def teardown_module(_module):
    shutil.rmtree(_FAKE_HOME, ignore_errors=True)


# ---------------------------------------------------------------------------
# 1. 顶层包 & 子模块导入
# ---------------------------------------------------------------------------


def test_top_level_import_exposes_public_api():
    assert hasattr(funhub, "RepoManager")
    assert hasattr(funhub, "repo_manager")
    assert hasattr(funhub, "base_config")
    assert hasattr(funhub, "BaseProvider")
    assert hasattr(funhub, "SyncResult")
    assert hasattr(funhub, "GitHubProvider")
    assert hasattr(funhub, "HuggingFaceProvider")


def test_submodule_imports():
    import funhub.base
    import funhub.base.config
    import funhub.base.provider
    import funhub.manager
    import funhub.providers
    import funhub.providers.github
    import funhub.providers.huggingface
    import funhub.cli

    assert funhub.base and funhub.manager and funhub.providers and funhub.cli


# ---------------------------------------------------------------------------
# 2. SyncResult —— 纯数据对象
# ---------------------------------------------------------------------------


def test_sync_result_defaults():
    r = SyncResult(True)
    assert r.success is True
    assert r.fid is None
    assert r.metadata == {}


def test_sync_result_with_values():
    r = SyncResult(False, fid="abc", message="oops", metadata={"k": "v"})
    assert r.success is False
    assert "abc" in str(r)
    assert r.metadata == {"k": "v"}


# ---------------------------------------------------------------------------
# 3. Config —— 使用 tmp_path，不触碰真实 HOME
# ---------------------------------------------------------------------------


def test_config_default_config_when_missing(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg = Config(config_path=str(cfg_path))
    assert cfg.get("storage.github_path") == "github"
    assert cfg.get("network.timeout") == 30
    assert cfg.get("no.such.key", "default") == "default"


def test_config_get_set_save_roundtrip(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg = Config(config_path=str(cfg_path))
    cfg.set("storage.base_path", "/tmp/somewhere")
    cfg.save_config()
    assert cfg_path.exists()

    cfg2 = Config(config_path=str(cfg_path))
    assert cfg2.get("storage.base_path") == "/tmp/somewhere"


def test_config_get_storage_path(tmp_path):
    cfg_path = tmp_path / "config.yaml"
    cfg = Config(config_path=str(cfg_path))
    p = cfg.get_storage_path("github", "octocat", "hello-world")
    assert str(p) == str(cfg.base_storage_path / "github" / "octocat" / "hello-world")


# ---------------------------------------------------------------------------
# 4. BaseProvider —— 抽象基类
# ---------------------------------------------------------------------------


def test_base_provider_is_abstract():
    with pytest.raises(TypeError):
        BaseProvider("dummy")


def test_provider_validate_repo_name():
    provider = GitHubProvider(drive=MagicMock())
    assert provider.validate_repo_name("octocat", "hello-world") is True
    assert provider.validate_repo_name("", "hello-world") is False
    assert provider.validate_repo_name("octo:cat", "hello-world") is False


# ---------------------------------------------------------------------------
# 5. GitHubProvider / HuggingFaceProvider —— URL 解析(纯逻辑) + 网络请求打桩
# ---------------------------------------------------------------------------


def test_github_provider_parse_url():
    provider = GitHubProvider(drive=MagicMock())
    assert provider.parse_url("https://github.com/octocat/hello-world") == (
        "octocat",
        "hello-world",
    )


def test_github_provider_parse_url_strips_git_suffix():
    provider = GitHubProvider(drive=MagicMock())
    assert provider.parse_url("https://github.com/octocat/hello-world.git") == (
        "octocat",
        "hello-world",
    )


def test_huggingface_provider_parse_url():
    provider = HuggingFaceProvider(drive=MagicMock())
    assert provider.parse_url("https://huggingface.co/bert-base-uncased/model") == (
        "bert-base-uncased",
        "model",
    )


@patch("funhub.providers.github.requests.get")
def test_github_provider_get_repo_info_mocked(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "name": "hello-world",
        "full_name": "octocat/hello-world",
        "description": "test",
        "stargazers_count": 1,
    }
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    provider = GitHubProvider(drive=MagicMock())
    info = provider.get_repo_info("octocat", "hello-world")

    assert info["name"] == "hello-world"
    mock_get.assert_called_once()


@patch("funhub.providers.huggingface.requests.get")
def test_huggingface_provider_get_repo_info_mocked(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"id": "org/model", "description": "test"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response

    provider = HuggingFaceProvider(drive=MagicMock())
    info = provider.get_repo_info("org", "model")

    assert info["full_name"] == "org/model"
    mock_get.assert_called_once()


# ---------------------------------------------------------------------------
# 6. RepoManager —— 构造 & 无网络路径
# ---------------------------------------------------------------------------


def test_repo_manager_registers_providers():
    manager = RepoManager(drive=MagicMock())
    assert "github" in manager.providers
    assert "huggingface" in manager.providers


def test_repo_manager_sync_repo_unrecognized_source_no_network():
    # 未知域名会在 _identify_source 阶段直接返回失败，不会发起任何网络请求。
    manager = RepoManager(drive=MagicMock())
    result = manager.sync_repo("https://example.com/foo/bar")
    assert result.success is False
    assert "无法识别仓库来源" in result.message


def test_repo_manager_get_repo_fid_missing_returns_none():
    manager = RepoManager(drive=MagicMock())
    assert manager.get_repo_fid("github", "no", "such", "main") is None


def test_repo_manager_list_synced_repos_empty():
    manager = RepoManager(drive=MagicMock())
    assert manager.list_synced_repos() == []


# 已知问题（不在本次冒烟测试范围内修复，仅记录）：
# funhub/manager.py 的 RepoManager._load_sync_records() 引用了未导入的
# 名字 `config`（很可能应为同模块可用的 `base_config`），每次构造
# RepoManager() 都会触发 NameError。该异常被方法内的
# `except Exception` 吞掉，只打一条 ERROR 日志，`self.sync_records`
# 回退为空字典，因此不会导致导入/构造失败，也不影响本冒烟测试套件通过。
# 但这意味着"加载已有同步记录"这个功能实际上从未生效——已在 PR/issue
# 中报告，未在此修复，避免超出"轻量冒烟测试"的范围改动业务逻辑。


# ---------------------------------------------------------------------------
# 7. CLI 入口 —— `funhub --help` 等
# ---------------------------------------------------------------------------


def test_cli_help_exits_cleanly():
    from click.testing import CliRunner
    from funhub.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "FunHub" in result.output


def test_cli_subcommand_help_exits_cleanly():
    from click.testing import CliRunner
    from funhub.cli import main

    runner = CliRunner()
    for args in (["sync", "--help"], ["list", "--help"], ["config", "--help"]):
        result = runner.invoke(main, args)
        assert result.exit_code == 0, f"{args} failed: {result.output}"
