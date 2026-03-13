#!/usr/bin/env python3
"""
GitHub OAuth2 授权管理模块
提供OAuth2认证、令牌管理和自动刷新功能
"""

import requests
import json
import webbrowser
import urllib.parse
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from typing import Dict, List, Optional


class GitHubOAuth:
    """GitHub OAuth2 授权管理器"""

    AUTH_URL = "https://github.com/login/oauth/authorize"
    TOKEN_URL = "https://github.com/login/oauth/access_token"
    DEFAULT_REDIRECT_URI = "http://localhost:8080/callback"
    DEFAULT_SCOPES = ["repo", "user", "read:org"]

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ):
        """
        初始化 OAuth 客户端

        Args:
            client_id: 应用客户端ID
            client_secret: 应用客户端密钥
            redirect_uri: 回调地址，默认 http://localhost:8080/callback
            scopes: 授权范围列表
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri or self.DEFAULT_REDIRECT_URI
        self.scopes = scopes or self.DEFAULT_SCOPES
        self.access_token = None
        self.refresh_token = None
        self.token_type = "bearer"
        self.expires_in = None
        self.created_at = None

    def get_authorization_url(self, state: Optional[str] = None) -> str:
        """
        生成授权URL

        Args:
            state: 可选的状态参数，用于防止CSRF攻击

        Returns:
            授权URL
        """
        if state is None:
            import uuid
            state = str(uuid.uuid4())

        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": " ".join(self.scopes),
            "state": state,
        }

        url = f"{self.AUTH_URL}?{urllib.parse.urlencode(params)}"
        return url

    def authorize_interactive(self) -> bool:
        """
        交互式授权流程（在浏览器中打开授权页面）

        Returns:
            授权是否成功
        """
        # 创建本地HTTP服务器接收回调
        auth_code = []
        server_running = [True]

        class CallbackHandler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path.startswith("/callback"):
                    # 解析授权码
                    query = urllib.parse.urlparse(self.path).query
                    params = urllib.parse.parse_qs(query)

                    if "code" in params:
                        auth_code.append(params["code"][0])
                        # 返回成功页面
                        self.send_response(200)
                        self.send_header("Content-type", "text/html; charset=utf-8")
                        self.end_headers()
                        success_html = """
                            <html><head><title>授权成功</title></head>
                            <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
                                <h1 style="color: #4CAF50;">&#10003; 授权成功!</h1>
                                <p>您可以关闭此页面并返回终端。</p>
                                <script>window.close();</script>
                            </body></html>
                        """
                        self.wfile.write(success_html.encode("utf-8"))
                        server_running[0] = False
                    elif "error" in params:
                        error = params["error"][0]
                        error_description = params.get("error_description", [""])[0]
                        self.send_response(400)
                        self.send_header("Content-type", "text/html; charset=utf-8")
                        self.end_headers()
                        html_content = f"""
                            <html><head><title>授权失败</title></head>
                            <body style="font-family: Arial, sans-serif; text-align: center; padding-top: 50px;">
                                <h1 style="color: #f44336;">❌ 授权失败</h1>
                                <p>错误: {error}</p>
                                <p>{error_description}</p>
                            </body></html>
                            """
                        self.wfile.write(html_content.encode("utf-8"))
                        server_running[0] = False

            def log_message(self, format, *args):
                pass  # 静默模式

        # 启动本地服务器
        port = 8080
        server = HTTPServer(("localhost", port), CallbackHandler)
        server_thread = Thread(target=server.serve_forever, daemon=True)
        server_thread.start()

        # 打开浏览器进行授权
        auth_url = self.get_authorization_url()
        print(f"\n🌐 正在打开浏览器进行授权...")
        print(f"📍 如果浏览器没有自动打开，请访问: {auth_url}")
        webbrowser.open(auth_url)

        # 等待回调
        print("⏳ 等待授权回调...")
        timeout = 120  # 2分钟超时
        start_time = time.time()

        while server_running[0] and (time.time() - start_time) < timeout:
            time.sleep(0.5)

        server.shutdown()

        if not auth_code:
            print("❌ 授权超时或失败")
            return False

        # 使用授权码获取访问令牌
        code = auth_code[0]
        return self.get_token_with_code(code)

    def get_token_with_code(self, code: str) -> bool:
        """
        使用授权码获取访问令牌

        Args:
            code: 授权码

        Returns:
            是否成功获取令牌
        """
        print("🔑 正在交换访问令牌...")

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": self.redirect_uri,
        }

        headers = {
            "Accept": "application/json",
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "bearer")
            self.expires_in = token_data.get("expires_in")
            self.created_at = token_data.get("created_at", int(time.time()))

            print("✅ 成功获取访问令牌!")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ 获取令牌失败: {e}")
            return False

    def get_token_with_password(self, username: str, password: str) -> bool:
        """
        使用密码模式获取访问令牌（GitHub 不支持此模式）

        Args:
            username: GitHub 用户名
            password: GitHub 密码

        Returns:
            是否成功获取令牌
        """
        print("❌ GitHub 不支持密码模式，请使用 authorize_interactive() 方法")
        return False

    def refresh_access_token(self) -> bool:
        """
        刷新访问令牌（GitHub OAuth 应用不返回 refresh_token）

        Returns:
            是否成功刷新
        """
        if not self.refresh_token:
            print("⚠️  GitHub OAuth 不提供 refresh_token")
            print("   建议: 重新运行 authorize_interactive() 获取新令牌")
            return False

        print("🔄 正在刷新访问令牌...")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        headers = {
            "Accept": "application/json",
        }

        try:
            response = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=10)
            response.raise_for_status()
            token_data = response.json()

            self.access_token = token_data.get("access_token")
            # 有些实现会返回新的 refresh_token
            new_refresh = token_data.get("refresh_token")
            if new_refresh:
                self.refresh_token = new_refresh
            self.created_at = token_data.get("created_at", int(time.time()))

            print("✅ 成功刷新访问令牌!")
            return True

        except requests.exceptions.RequestException as e:
            print(f"❌ 刷新令牌失败: {e}")
            return False

    def is_token_expired(self) -> bool:
        """
        检查令牌是否过期

        Returns:
            是否过期
        """
        if not self.created_at or not self.expires_in:
            return False

        expire_time = self.created_at + self.expires_in
        # 提前5分钟认为过期
        return time.time() > (expire_time - 300)

    def save_to_file(self, filepath: str = ".github_token.json"):
        """
        保存令牌到文件

        Args:
            filepath: 文件路径
        """
        token_data = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "created_at": self.created_at,
        }

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(token_data, f, indent=2)
            print(f"💾 令牌已保存到: {filepath}")
        except Exception as e:
            print(f"❌ 保存令牌失败: {e}")

    def load_from_file(self, filepath: str = ".github_token.json") -> bool:
        """
        从文件加载令牌

        Args:
            filepath: 文件路径

        Returns:
            是否成功加载
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                token_data = json.load(f)

            self.access_token = token_data.get("access_token")
            self.refresh_token = token_data.get("refresh_token")
            self.token_type = token_data.get("token_type", "bearer")
            self.expires_in = token_data.get("expires_in")
            self.created_at = token_data.get("created_at")

            if self.access_token:
                print(f"📖 已从 {filepath} 加载令牌")
                return True
            return False

        except FileNotFoundError:
            print(f"⚠️  令牌文件不存在: {filepath}")
            return False
        except Exception as e:
            print(f"❌ 加载令牌失败: {e}")
            return False
