# Gitee/GitHub API 爬虫示例

这是一个支持 Gitee 和 GitHub 的 Python 代码爬虫程序，支持 OAuth2 授权和代码文件爬取。

### 基础功能
-  获取仓库基本信息（名称、描述、stars、forks等）
-  获取README内容
-  获取Issues列表
-  搜索仓库功能 - 使用浏览器自动化工具（支持 Gitee 网页搜索）

### 代码爬取功能
-  **代码文件爬取**：递归爬取仓库的所有代码文件
-  **文件过滤**：按扩展名过滤文件类型
-  **本地保存**：保持原始目录结构保存到本地

### Issue 爬取功能
-  **精简格式**：只保存核心信息（标题、正文、评论）
-  **完整对话**：自动获取 issue 和评论的完整内容
-  **状态过滤**：支持 open/closed/all 三种状态

### 认证功能
-  **OAuth2 授权**：完整的 OAuth2 授权流程，支持自动刷新令牌
-  **Access Token**：支持使用访问令牌进行认证
-  **令牌管理**：自动保存和加载访问令牌

## 快速开始

### 1. 安装依赖
```bash
# 使用 uv（推荐，更快的包管理器）
uv pip install -r requirements.txt

# 或使用传统 pip
pip install -r requirements.txt
```

**注意**: Gitee 搜索功能根据实际情况， 可以使用 Google Chrome 浏览器，无需下载额外的 Chromium。

### 2. 配置认证 (推荐但可选)

创建 `.env` 文件：

**Gitee 平台配置：**
```bash
# 方式1: 使用 Access Token (推荐)
GITEE_ACCESS_TOKEN=your_access_token_here

# 方式2: 使用 OAuth2 (最高限额)
GITEE_CLIENT_ID=your_client_id
GITEE_CLIENT_SECRET=your_client_secret

# 选择平台 (可选，默认 gitee)
CRAWL_PLATFORM=gitee
```

**GitHub 平台配置：**
```bash
# 方式1: 使用 Personal Access Token (推荐)
GITHUB_ACCESS_TOKEN=ghp_your_access_token_here

# 方式2: 使用 OAuth2
GITHUB_CLIENT_ID=your_client_id
GITHUB_CLIENT_SECRET=your_client_secret

# 选择平台
CRAWL_PLATFORM=github
```

获取 Access Token：
- Gitee: https://gitee.com/profile/personal_access_tokens
- GitHub: https://github.com/settings/tokens

### 3. 使用 AscendC 爬虫 

#### 基本使用
```bash
# 使用默认配置爬取 (Gitee平台)
python main_crawler.py

# 使用 GitHub 平台
python main_crawler.py --platform github

# 指定搜索关键词
python main_crawler.py --keywords "AscendC,CANN"

# 限制爬取数量
python main_crawler.py --max-repos 5 --max-files 50

# 爬取 Issues（包含完整评论）
python main_crawler.py --crawl-issues --issue-state all --max-issues 100

# 只搜索不下载
python main_crawler.py --search-only

# 查看所有选项
python main_crawler.py --help
```

#### 平台选择
```bash
# 使用 Gitee (默认)
python main_crawler.py --platform gitee

# 使用 GitHub
python main_crawler.py --platform github -p github
```

#### 使用配置文件
```bash
# 复制示例配置
cp config_example.json my_config.json

# 使用配置文件运行
python main_crawler.py --config my_config.json
```

#### 断点续传
```bash
# 从之前的进度文件恢复
python main_crawler.py --resume output/results/crawl_progress_20250101_120000.json
```

#### 环境变量配置
```bash
# 设置环境变量
export ASCENDC_MAX_REPOS=20
export ASCENDC_MIN_STARS=10
export ASCENDC_OUTPUT_DIR=output/my_crawl

# 运行爬虫
python main_crawler.py
```

### 4. 作为模块导入使用

#### 使用 Gitee 平台
```python
from adapters.gitee import GiteeAPI, GiteeCrawler, GiteeOAuth

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

#### 使用 GitHub 平台
```python
from adapters.github import GitHubAPI, GitHubCrawler, GitHubOAuth

# 使用 API 客户端
api = GitHubAPI(access_token="ghp_your_token")
repo_info = api.get_repo("owner", "repo")

# 使用爬虫
crawler = GitHubCrawler(api)
files = crawler.crawl_repo_files("owner", "repo", max_files=50)

# 使用 OAuth
oauth = GitHubOAuth(client_id="...", client_secret="...")
oauth.authorize_interactive()
api = GitHubAPI(oauth=oauth)
```

#### 统一接口（推荐）
```python
from core import BaseAPI, BaseCrawler

# 使用时根据平台选择具体的实现类
platform = "github"  # 或 "gitee"
if platform == "github":
    from adapters.github import GitHubAPI, GitHubCrawler
else:
    from adapters.gitee import GiteeAPI, GiteeCrawler
```

## 🔧 配置说明

### AscendC 爬虫配置选项

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--max-repos` | 最大爬取仓库数 | 10 |
| `--max-files` | 每个仓库最大文件数 | 100 |
| `--min-stars` | 最小 stars 数 | 0 |
| `--min-forks` | 最小 forks 数 | 0 |
| `--days` | 最近N天内更新 | 365 |
| `--keywords` | 搜索关键词 | AscendC,CANN,算子开发 |
| `--extensions` | 文件扩展名 | .py,.cpp,.h,.md 等 |
| `--output-dir` | 输出目录 | output/ascendc |
| `--results-dir` | 结果目录 | output/results |
| `--crawl-issues` | 启用 issue 爬取 | 否 |
| `--issue-state` | issue 状态 (open/closed/all) | all |
| `--max-issues` | 每个仓库最大 issue 数 | 100 |

### API 速率限制

**Gitee 平台：**
- **无认证**: 约 60 次/小时
- **Access Token**: 约 500 次/小时
- **OAuth2**: 约 5000 次/小时 (推荐)

**GitHub 平台：**
- **无认证**: 约 60 次/小时
- **Personal Access Token**: 约 5000 次/小时 (推荐)
- **OAuth2**: 约 5000 次/小时

## 📂 目录结构

```
crawlDemo/
├── main_crawler.py          # AscendC 爬虫主程序 (生产级)
├── crawl_ascendC.py         # AscendC 爬虫模块
├── config.py                # 配置管理模块
├── config_example.json      # 示例配置文件
├── utils.py                 # 工具函数
├── requirements.txt         # 依赖列表
├── core/                    # 核心抽象层
│   ├── __init__.py
│   ├── base_api.py         # API 基类
│   └── base_crawler.py     # 爬虫基类
│
├── adapters/                # 平台适配器
│   ├── __init__.py
│   ├── gitee/              # Gitee 适配器
│   │   ├── __init__.py
│   │   ├── api.py          # GiteeAPI 实现
│   │   ├── crawler.py      # GiteeCrawler 实现
│   │   ├── oauth.py        # Gitee OAuth 实现
│   │   └── search.py       # Gitee 网页搜索实现
│   └── github/             # GitHub 适配器
│       ├── __init__.py
│       ├── api.py          # GitHubAPI 实现
│       ├── crawler.py      # GitHubCrawler 实现
│       └── oauth.py        # GitHub OAuth 实现
│
├── output/                  # 输出目录
│   ├── ascendc/            # 爬取的代码
│   │   └── {owner}_{repo}/
│   │       ├── files/      # 代码文件
│   │       └── issues/     # Issues（精简格式）
│   │           ├── issues_index.json
│   │           └── issue_*.json
│   └── results/            # 爬取结果 JSON
├── logs/                   # 日志目录
│   └── ascendc_crawler.log
├── QUICK_START.md          # 快速开始指南
└── CLAUDE.md               # Claude Code 项目文档
```


## 🐛 故障排查

### 常见问题

**Q: 提示认证失败或速率限制**
```bash
# Gitee 解决方法: 配置 Access Token 或 OAuth2
export GITEE_ACCESS_TOKEN=your_token

# GitHub 解决方法: 配置 Personal Access Token
export GITHUB_ACCESS_TOKEN=ghp_your_token
```

**Q: 找不到相关仓库**
```bash
# 解决方法: 调整搜索关键词和过滤条件
python main_crawler.py --keywords "AscendC" --min-stars 0

# 尝试切换平台
python main_crawler.py --platform github
```

**Q: 下载速度慢**
```bash
# 解决方法: 减少爬取数量
python main_crawler.py --max-repos 3 --max-files 50
```

**Q: 搜索功能启动浏览器失败**
```bash
# 确保系统已安装 Google Chrome
# macOS:
which "Google Chrome"

# Linux:
which google-chrome-stable

# Windows:
where chrome

# 如果未安装，请先安装 Chrome 浏览器
```

## License

MIT License
