# Gitee API 爬虫示例

这是一个使用 Gitee API v5 爬取仓库信息的 Python 示例程序，支持 OAuth2 授权和代码文件爬取。

## 功能特性

### AscendC 爬虫功能
- 🔍 **多关键词搜索**：自动搜索 AscendC、CANN、算子开发等相关仓库
- 📊 **智能筛选**：按 stars、forks、更新时间过滤
- 📥 **批量下载**：批量爬取多个仓库的代码文件
- 💾 **进度保存**：定期保存进度，支持中断恢复
- 📈 **统计分析**：生成详细的爬取报告和统计数据
- 🎯 **文件过滤**：按扩展名过滤文件类型
- 📝 **完善日志**：所有操作都有详细日志记录

### 基础功能
-  获取仓库基本信息（名称、描述、stars、forks等）
-  获取README内容
-  获取Issues列表
-  搜索仓库功能

### 代码爬取功能
-  **代码文件爬取**：递归爬取仓库的所有代码文件
-  **文件过滤**：按扩展名过滤文件类型
-  **本地保存**：保持原始目录结构保存到本地

### 认证功能
-  **OAuth2 授权**：完整的 OAuth2 授权流程，支持自动刷新令牌
-  **Access Token**：支持使用访问令牌进行认证
-  **令牌管理**：自动保存和加载访问令牌

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置认证 (推荐但可选)

创建 `.env` 文件：
```bash
# 方式1: 使用 Access Token (推荐)
GITEE_ACCESS_TOKEN=your_access_token_here

# 方式2: 使用 OAuth2 (最高限额)
GITEE_CLIENT_ID=your_client_id
GITEE_CLIENT_SECRET=your_client_secret
```

获取 Access Token: https://gitee.com/profile/personal_access_tokens

### 3. 使用 AscendC 爬虫 (生产级)

#### 基本使用
```bash
# 使用默认配置爬取
python main_crawler.py

# 指定搜索关键词
python main_crawler.py --keywords "AscendC,CANN"

# 限制爬取数量
python main_crawler.py --max-repos 5 --max-files 50

# 只搜索不下载
python main_crawler.py --search-only

# 查看所有选项
python main_crawler.py --help
```

#### 使用配置文件
```bash
# 复制示例配置
cp config_example.json my_config.json

# 编辑配置文件
vim my_config.json

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


### 4.作为模块导入使用

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

### API 速率限制

- **无认证**: 约 60 次/小时
- **Access Token**: 约 500 次/小时
- **OAuth2**: 约 5000 次/小时 (推荐)

## 📂 目录结构

```
crawlDemo/
├── main_crawler.py          # AscendC 爬虫主程序 (生产级)
├── crawl_ascendC.py         # AscendC 爬虫模块
├── config.py                # 配置管理模块
├── config_example.json      # 示例配置文件
├── gitee_api.py             # Gitee API 客户端
├── gitee_crawler.py         # 通用爬虫模块
├── gitee_oauth.py           # OAuth2 授权模块
├── utils.py                 # 工具函数
├── requirements.txt         # 依赖列表
├── output/                  # 输出目录
│   ├── ascendc/            # 爬取的代码
│   └── results/            # 爬取结果 JSON
└── logs/                   # 日志目录
    └── ascendc_crawler.log
```

## 🛠️ 高级功能

### 扩展性设计

代码采用模块化设计，便于扩展到其他平台：

1. **统一接口 + 多适配器模式**
   - 定义统一的爬虫接口 `BaseCrawler`
   - 为每个平台实现适配器 (Gitee, GitHub, Blog)
   - 添加新平台只需实现接口，无需修改现有代码

2. **配置驱动**
   - 支持配置文件、命令行参数、环境变量
   - 平台配置集中管理 (未来支持)

3. **可扩展架构**
   ```
   core/               # 核心抽象层
   ├── base_crawler.py # 爬虫基类
   └── models.py       # 数据模型

   adapters/           # 平台适配器
   ├── gitee/          # Gitee 适配器 ✅
   ├── github/         # GitHub 适配器 (规划中)
   └── blog/           # Blog 适配器 (规划中)
   ```

### 未来规划

- [ ] GitHub 代码爬取支持
- [ ] 技术文档站点爬取 (Blog适配器)
- [ ] 个人博客 RSS 订阅支持
- [ ] 多线程并发爬取
- [ ] 更智能的代码去重
- [ ] Web UI 界面

## 🐛 故障排查

### 常见问题

**Q: 提示认证失败或速率限制**
```bash
# 解决方法: 配置 Access Token 或 OAuth2
export GITEE_ACCESS_TOKEN=your_token
```

**Q: 找不到相关仓库**
```bash
# 解决方法: 调整搜索关键词和过滤条件
python main_crawler.py --keywords "AscendC" --min-stars 0
```

**Q: 下载速度慢**
```bash
# 解决方法: 减少爬取数量
python main_crawler.py --max-repos 3 --max-files 50
```

## License

MIT License
