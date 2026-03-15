# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Instruction

1. 在编写代码之前，请描述你的方案并等待批准，如果需求不明确，在编写代码之前务必进行澄清。

## Project Overview

This is a **Gitee API crawler** - a Python application that interacts with the Gitee API v5 to fetch repository information. Gitee is a Git-based code hosting platform popular in China. The project demonstrates API client patterns and web scraping techniques for educational purposes.

## Running the Application

### Installation

**重要提示**: 本项目使用 `uv` 作为包管理工具，安装依赖时请使用：

```bash
# 安装所有依赖
uv pip install -r requirements.txt

# 安装单个包
uv pip install <package-name>
```

**为什么不使用 pip**: `uv` 是一个更快的 Python 包管理器，由 Astral（Rust 团队）开发，比传统 pip 快 10-100 倍。

### Gitee 搜索功能说明

由于 Gitee 的搜索 API (`/search/repositories`) 已失效，项目现在使用 Playwright 浏览器自动化工具来实现网页搜索功能。

**搜索功能特点**:
- ✅ 使用系统已安装的 Chrome 浏览器（无需下载额外的 Chromium）
- ✅ 支持无头模式（headless）和可视化模式
- ✅ 自动解析 Gitee 搜索结果页面
- ✅ 完全兼容现有的 API 接口

**搜索模块位置**: `adapters/gitee/search.py`

**使用示例**:
```python
from adapters.gitee import GiteeAPI

api = GiteeAPI()
results = api.search_repositories('AscendC', per_page=10)
```

### Run the main demo
```bash
python crawl_ascendC.py
```

测试搜索功能：
```bash
python test_search.py
```

The main entry point is `crawl_ascendC.py`. The `gitee_api_demo.py` file is a legacy demo.

## Architecture

### Core Components

**`GiteeAPI` class** (gitee_api_demo.py:349-)
- Central API client that encapsulates all Gitee API interactions
- Uses `requests.Session` for connection pooling and persistent HTTP connections
- Implements optional authentication via access token or OAuth
- Provides a unified `_get()` method that handles:
  - Token injection (supports both access_token and OAuth tokens)
  - Error handling with `requests.exceptions.RequestException`
  - 10-second timeout for all requests

**API Endpoint Methods**
Each method in `GiteeAPI` maps to a specific Gitee API endpoint:
- `get_repo()` - Repository metadata
- `get_repo_readme()` - README content (with base64 decoding)
- `get_repo_issues()` - Issues list (open/closed)
- `get_repo_contents()` - Directory contents
- `get_file_content()` - File content with base64 decoding
- `crawl_repo_files()` - Recursive file crawler with extension filtering
- `save_repo_files()` - Save crawled files to local disk

**Demo Functions**
- `demo_crawl_gitee_repo()` - Main demo that fetches repository info, README, and issues
- `demo_crawl_code_files()` - Demonstrates code file crawling functionality
- `demo_search_repositories()` - Demonstrates repository search functionality
- `demo_oauth_authorization()` - Demonstrates OAuth2 authorization flow

### Design Patterns

1. **API Client Pattern** - `GiteeAPI` class provides a clean interface to complex API endpoints
2. **Session Management** - Uses `requests.Session()` for efficient connection reuse
3. **Facade Pattern** - Simplifies API interactions behind method calls
4. **Builder Pattern** - `_get()` method acts as a generic request builder with centralized error handling

### Data Flow

```
User runs script → demo_crawl_gitee_repo()
    ↓
GiteeAPI instance created (with optional token)
    ↓
Multiple API method calls (get_repo, get_repo_branches, etc.)
    ↓
Each method builds endpoint and calls _get()
    ↓
_get() adds auth token, sends HTTP request
    ↓
Response parsed from JSON and returned
    ↓
Data printed to console with print_json()
```

## Configuration

### Changing Target Repository
Edit `demo_crawl_gitee_repo()` in gitee_api_demo.py:192-193:
```python
owner = "your-owner"      # Repository owner
repo = "your-repo"        # Repository name
```

### Using Access Token (Optional)
For higher API rate limits:
```python
access_token = "your_access_token_here"
api = GiteeAPI(access_token=access_token)
```

Get tokens from: https://gitee.com/settings/applications

### Using OAuth2 (Optional)
For highest API rate limits and automatic token refresh:
```python
oauth = GiteeOAuth(client_id="your_client_id", client_secret="your_client_secret")
if oauth.load_from_file() or oauth.authorize_interactive():
    api = GiteeAPI(oauth=oauth)
```

Create OAuth app at: https://gitee.com/settings/applications

## Key Implementation Details

- **Base URL**: `https://gitee.com/api/v5`
- **Default headers**: User-Agent set to "Gitee-API-Demo/1.0", Content-Type to "application/json"
- **Authentication**: Token passed as query parameter (not Bearer header)
- **Pagination**: Most endpoints use `per_page` parameter (default values: 20-100)
- **Error handling**: Returns empty dict/list on request failures, prints error message
- **Branch default**: Uses "master" as default branch for commits

## Dependencies

- **requests>=2.31.0** - The only external dependency for HTTP requests
- **Standard library**: json, typing

## API Reference

Full Gitee API v5 documentation: https://gitee.com/api/v5/swagger

Key endpoints used:
- `GET /repos/{owner}/{repo}` - Repository info
- `GET /repos/{owner}/{repo}/readme` - README
- `GET /repos/{owner}/{repo}/issues` - Issues
- `GET /repos/{owner}/{repo}/contents/{path}` - File contents
- `GET /search/repositories` - Search repositories

## Sample Output

See `demo_result.json` for an example of the JSON structure returned by the API. The file contains results from crawling `harrygt/ascendc-tutorial`.

## Language Note

The codebase contains Chinese comments and documentation (README.md), but all code identifiers and API interactions are in English.
