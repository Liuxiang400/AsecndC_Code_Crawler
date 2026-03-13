# Gitee API 爬虫示例

这是一个使用 Gitee API v5 爬取仓库信息的 Python 示例程序，支持 OAuth2 授权和代码文件爬取。

## 功能特性

### 基础功能
- ✅ 获取仓库基本信息（名称、描述、stars、forks等）
- ✅ 获取README内容
- ✅ 获取Issues列表
- ✅ 搜索仓库功能

### 代码爬取功能
- ✅ **代码文件爬取**：递归爬取仓库的所有代码文件
- ✅ **文件过滤**：按扩展名过滤文件类型
- ✅ **本地保存**：保持原始目录结构保存到本地

### 认证功能
- ✅ **OAuth2 授权**：完整的 OAuth2 授权流程，支持自动刷新令牌
- ✅ **Access Token**：支持使用访问令牌进行认证
- ✅ **令牌管理**：自动保存和加载访问令牌

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行程序

```bash
python gitee_api_demo.py
```

可选的命令行参数：
```bash
python gitee_api_demo.py basic   # 基础仓库信息爬取
python gitee_api_demo.py code    # 代码文件爬取
python gitee_api_demo.py oauth   # OAuth2 授权演示
python gitee_api_demo.py search  # 仓库搜索
```

### 3.作为模块导入使用

```python
from gitee_api import GiteeAPI
from gitee_crawler import GiteeCrawler
from gitee_oauth import GiteeOAuth

# 使用 API 客户端
api = GiteeAPI(access_token="your_token")
repo_info = api.get_repo("owner", "repo")

# 使用爬虫
crawler = GiteeCrawler(api)
files = crawler.crawl_repo_files("owner", "repo", max_files=50)

# 使用 OAuth
oauth = GiteeOAuth(client_id="...", client_secret="...")
oauth.authorize_interactive()
api = GiteeAPI(oauth=oauth)
```

### 4. 认证方式（三选一）

#### 方式一：无认证（最低限额）
```python
from gitee_api_demo import GiteeAPI

api = GiteeAPI()
```
限额：约 60 次/小时

#### 方式二：Access Token（中等限额）

**通过环境变量设置（推荐）：**
```bash
# 在终端中设置
export GITEE_ACCESS_TOKEN="your_access_token_here"
```

**通过代码设置：**
```python
import os
access_token = os.getenv("GITEE_ACCESS_TOKEN")
api = GiteeAPI(access_token=access_token)
```

限额：约 500 次/小时

#### 方式三：OAuth2 授权（最高限额，推荐）
```bash
python oauth_demo.py
```
或运行主程序选择 `oauth` 选项。

限额：约 5000 次/小时

## 参考文档

- **Gitee API 官方文档**: https://gitee.com/api/v5/swagger
- **OAuth2 官方文档**: https://gitee.com/api/v5/oauth_doc
- **OAuth2 RFC 6749**: https://tools.ietf.org/html/rfc6749

## License

MIT License
