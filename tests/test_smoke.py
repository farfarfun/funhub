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
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# 必须在 `import funhub` 之前重定向 HOME，防止污染开发者真实的 ~/.funhub。
# ---------------------------------------------------------------------------
_FAKE_HOME = tempfile.mkdtemp(prefix="funhub_test_home_")
os.environ["HOME"] = _FAKE_HOME

import funhub
from funhub.base.config import Config
from funhub.base.provider import BaseProvider, SyncResult
from funhub.manager import RepoManager
from funhub.providers.github import GitHubProvider
from funhub.providers.huggingface import HuggingFaceProvider


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
    import funhub.cli
    import funhub.manager
    import funhub.providers
    import funhub.providers.github
    import funhub.providers.huggingface

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


def test_repo_manager_sync_repo_success_persists_record():
    """同步成功后记录应写入磁盘，且能被新的 RepoManager 实例重新加载。"""
    manager = RepoManager(drive=MagicMock())
    fake_provider = MagicMock()
    fake_provider.parse_url.return_value = ("octocat", "hello-world")
    fake_provider.validate_repo_name.return_value = True
    fake_provider.sync_repo_to_drive.return_value = SyncResult(
        True, fid="fid-123", message="ok", metadata={"k": "v"}
    )
    manager.providers["github"] = fake_provider

    result = manager.sync_repo("https://github.com/octocat/hello-world")

    assert result.success is True
    assert result.fid == "fid-123"
    record_key = "github/octocat/hello-world/main"
    assert record_key in manager.sync_records
    assert manager.sync_records[record_key]["fid"] == "fid-123"

    # 重新构造 RepoManager，验证同步记录能从磁盘正确加载（回归：
    # 此前 _load_sync_records 引用未导入的 `config` 触发 NameError，
    # 被 except Exception 吞掉后记录永远无法持久化/加载）。
    reloaded = RepoManager(drive=MagicMock())
    assert reloaded.sync_records.get(record_key, {}).get("fid") == "fid-123"


def test_repo_manager_sync_repo_existing_record_skips_provider_call():
    manager = RepoManager(drive=MagicMock())
    fake_provider = MagicMock()
    fake_provider.parse_url.return_value = ("octocat", "hello-world")
    fake_provider.validate_repo_name.return_value = True
    manager.providers["github"] = fake_provider
    record_key = "github/octocat/hello-world/main"
    manager.sync_records[record_key] = {"fid": "cached-fid"}

    result = manager.sync_repo("https://github.com/octocat/hello-world")

    assert result.success is True
    assert result.fid == "cached-fid"
    fake_provider.sync_repo_to_drive.assert_not_called()


def test_repo_manager_remove_sync_record_success_and_failure():
    manager = RepoManager(drive=MagicMock())
    record_key = "github/octocat/hello-world/main"
    manager.sync_records[record_key] = {"fid": "abc"}

    assert manager.remove_sync_record("github", "octocat", "hello-world") is True
    assert record_key not in manager.sync_records

    # 记录已不存在，应返回 False 而不是抛异常
    assert manager.remove_sync_record("github", "octocat", "hello-world") is False


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


def test_cli_version_option():
    from click.testing import CliRunner

    from funhub.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()
    assert "0.1.0" not in result.output  # 版本号必须随包元数据更新，不再硬编码


def test_cli_sync_success_exit_code_zero():
    from click.testing import CliRunner

    from funhub.cli import main

    with patch("funhub.cli.repo_manager") as mock_manager:
        mock_manager.sync_repo.return_value = SyncResult(
            True, fid="fid-1", message="ok"
        )
        runner = CliRunner()
        result = runner.invoke(main, ["sync", "https://github.com/octocat/hello-world"])

    assert result.exit_code == 0
    assert "fid-1" in result.output


def test_cli_sync_failure_exit_code_nonzero():
    from click.testing import CliRunner

    from funhub.cli import main

    with patch("funhub.cli.repo_manager") as mock_manager:
        mock_manager.sync_repo.return_value = SyncResult(False, message="下载失败")
        runner = CliRunner()
        result = runner.invoke(main, ["sync", "https://github.com/octocat/hello-world"])

    assert result.exit_code != 0
    assert "下载失败" in result.output


def test_cli_config_show_exits_cleanly():
    # 回归测试：此前 cli.py 通过 `from funhub.base import config` 拿到的是
    # 子模块对象而非 `base_config` 配置单例，调用 `.get()` 必然抛 AttributeError。
    from click.testing import CliRunner

    from funhub.cli import main

    runner = CliRunner()
    result = runner.invoke(main, ["config", "show"])

    assert result.exit_code == 0, result.output
    assert "存储路径" in result.output


def test_cli_config_set_and_init_exit_cleanly(tmp_path, monkeypatch):
    from click.testing import CliRunner

    from funhub.cli import main

    monkeypatch.setattr("funhub.cli.base_config.config_path", tmp_path / "config.yaml")

    runner = CliRunner()
    result = runner.invoke(main, ["config", "set", "network.timeout", "60"])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "config.yaml").exists()

    result = runner.invoke(main, ["config", "init"])
    assert result.exit_code == 0, result.output
