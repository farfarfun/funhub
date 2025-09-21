# FunHub API 文档

## 概述

FunHub 提供了完整的 API 来管理 Git 仓库到 fundrive 的同步功能。本文档详细说明了所有可用的类、方法和使用示例。

## 核心类

### BaseProvider

Git仓库提供者抽象基类，负责将不同Git平台的仓库同步到fundrive存储中。

#### 类定义

```python
class BaseProvider(ABC):
    """Git仓库提供者抽象基类"""
    
    def __init__(self, provider_name: str):
        """初始化提供者"""
```

#### 主要方法

##### sync_repo_to_drive()

```python
@abstractmethod
def sync_repo_to_drive(self, user: str, repo: str, branch: str = "main", 
                      force: bool = False) -> SyncResult:
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
```

##### get_repo_info()

```python
@abstractmethod
def get_repo_info(self, user: str, repo: str) -> Dict:
    """
    获取仓库基本信息
    
    Args:
        user: 用户名/组织名
        repo: 仓库名
        
    Returns:
        仓库信息字典
    """
```

##### parse_url()

```python
@abstractmethod
def parse_url(self, url: str) -> Tuple[str, str]:
    """
    解析仓库URL，提取用户名和仓库名
    
    Args:
        url: 仓库URL
        
    Returns:
        (用户名, 仓库名) 元组
    """
```

### SyncResult

同步结果类，封装同步操作的结果信息。

#### 类定义

```python
class SyncResult:
    """同步结果类"""
    
    def __init__(self, success: bool, fid: Optional[str] = None, 
                 message: str = "", metadata: Optional[Dict] = None):
        """
        初始化同步结果
        
        Args:
            success: 是否同步成功
            fid: fundrive中的文件ID，用于后续下载
            message: 结果消息
            metadata: 额外的元数据信息
        """
```

#### 字段说明

- `success`: 布尔值，表示同步是否成功
- `fid`: 字符串，fundrive中的文件ID，用于后续下载
- `message`: 字符串，同步结果的描述信息
- `metadata`: 字典，包含额外的元数据信息

### RepoManager

仓库管理器，负责协调不同提供者将Git仓库同步到fundrive。

#### 主要方法

##### sync_repo()

```python
def sync_repo(self, url: str, branch: str = "main", force: bool = False) -> SyncResult:
    """
    同步Git仓库到fundrive
    
    Args:
        url: 仓库URL
        branch: 分支名
        force: 是否强制重新同步
        
    Returns:
        SyncResult: 同步结果
    """
```

**使用示例：**

```python
from funhub import repo_manager

# 同步GitHub仓库
result = repo_manager.sync_repo("https://github.com/user/repo")
if result.success:
    print(f"同步成功，fid: {result.fid}")
else:
    print(f"同步失败: {result.message}")
```

##### list_synced_repos()

```python
def list_synced_repos(self, source: Optional[str] = None) -> List[Dict]:
    """
    列出已同步的仓库
    
    Args:
        source: 指定来源，None表示所有来源
        
    Returns:
        同步记录列表
    """
```

**使用示例：**

```python
# 列出所有已同步的仓库
repos = repo_manager.list_synced_repos()

# 只列出GitHub仓库
github_repos = repo_manager.list_synced_repos("github")
```

##### get_repo_fid()

```python
def get_repo_fid(self, source: str, user: str, repo: str, branch: str = "main") -> Optional[str]:
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
```

**使用示例：**

```python
# 获取仓库的fid
fid = repo_manager.get_repo_fid("github", "user", "repo")
if fid:
    print(f"仓库fid: {fid}")
    # 用户可以使用此fid通过fundrive下载
    # fundrive download {fid} ./target_folder
```

## 具体提供者

### GitHubProvider

GitHub仓库提供者，继承自BaseProvider。

#### 特殊方法

- 支持GitHub API获取仓库详细信息
- 支持代理配置
- 自动处理ZIP文件下载和上传

#### 返回的仓库信息字段

```python
{
    "name": "仓库名",
    "full_name": "完整名称",
    "description": "描述",
    "language": "主要编程语言",
    "stars": "星标数",
    "forks": "分叉数",
    "size": "仓库大小",
    "default_branch": "默认分支",
    "created_at": "创建时间",
    "updated_at": "更新时间",
    "clone_url": "克隆URL",
    "html_url": "网页URL"
}
```

### HuggingFaceProvider

HuggingFace仓库提供者，继承自BaseProvider。

#### 返回的仓库信息字段

```python
{
    "name": "仓库名",
    "full_name": "完整名称",
    "description": "描述",
    "tags": "标签列表",
    "pipeline_tag": "管道标签",
    "library_name": "库名称",
    "downloads": "下载次数",
    "likes": "点赞数",
    "created_at": "创建时间",
    "last_modified": "最后修改时间",
    "model_index": "模型索引",
    "private": "是否私有"
}
```

## 配置管理

### Config类

配置管理类，用于管理funhub的各种配置。

#### 主要方法

##### get()

```python
def get(self, key: str, default: Any = None) -> Any:
    """
    获取配置值
    
    Args:
        key: 配置键，支持点分隔的嵌套键
        default: 默认值
        
    Returns:
        配置值
    """
```

##### set()

```python
def set(self, key: str, value: Any):
    """
    设置配置值
    
    Args:
        key: 配置键，支持点分隔的嵌套键
        value: 配置值
    """
```

#### 默认配置

```python
{
    "storage": {
        "base_path": "~/fundrive",
        "github_path": "github",
        "huggingface_path": "huggingface",
        "gitee_path": "gitee"
    },
    "network": {
        "timeout": 30,
        "retry_times": 3,
        "proxy": {
            "http": None,
            "https": None
        }
    },
    "download": {
        "chunk_size": 8192,
        "max_workers": 4,
        "skip_existing": True
    }
}
```

## 命令行接口

### 主要命令

#### sync

同步Git仓库到fundrive。

```bash
funhub sync <url> [--force] [--branch <branch>]
```

**参数：**
- `url`: 仓库URL
- `--force, -f`: 强制重新同步
- `--branch, -b`: 指定分支名

#### list

列出已同步的仓库。

```bash
funhub list [--source <source>]
```

**参数：**
- `--source, -s`: 指定来源过滤

#### info

显示仓库信息和fid。

```bash
funhub info <source> <user> <repo> [--branch <branch>]
```

**参数：**
- `source`: 来源（github, huggingface等）
- `user`: 用户名
- `repo`: 仓库名
- `--branch, -b`: 分支名

#### remove

删除同步记录。

```bash
funhub remove <source> <user> <repo> [--branch <branch>]
```

## 使用示例

### 完整工作流程

```python
from funhub import repo_manager

# 1. 同步仓库
result = repo_manager.sync_repo("https://github.com/pytorch/pytorch")
if result.success:
    fid = result.fid
    print(f"同步成功，获得fid: {fid}")
    
    # 2. 用户使用fid通过fundrive下载（不经过funhub）
    # 这一步由用户在其他地方执行：
    # fundrive download {fid} ./pytorch
    
    # 3. 查看同步记录
    repos = repo_manager.list_synced_repos("github")
    for repo in repos:
        print(f"{repo['user']}/{repo['repo']} -> {repo['fid']}")
```

### 错误处理

```python
result = repo_manager.sync_repo("https://github.com/invalid/repo")
if not result.success:
    print(f"同步失败: {result.message}")
    # 处理错误情况
```

## 扩展开发

### 添加新的Git平台支持

1. 继承BaseProvider类
2. 实现必需的抽象方法
3. 在RepoManager中注册新提供者

```python
class CustomProvider(BaseProvider):
    def __init__(self):
        super().__init__("custom")
    
    def sync_repo_to_drive(self, user, repo, branch="main", force=False):
        # 实现同步逻辑
        pass
    
    def get_repo_info(self, user, repo):
        # 实现信息获取逻辑
        pass
    
    def parse_url(self, url):
        # 实现URL解析逻辑
        pass
```

## 注意事项

1. **解耦架构**：funhub只负责同步，不负责下载
2. **fid使用**：用户应该直接使用fid通过fundrive下载数据
3. **网络配置**：支持代理配置以解决访问问题
4. **错误处理**：所有操作都返回明确的结果状态
5. **配置管理**：支持灵活的配置自定义
