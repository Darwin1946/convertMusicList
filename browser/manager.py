import json
from pathlib import Path
from playwright.sync_api import sync_playwright, BrowserContext, Playwright

SESSION_FILE = Path("data/qqmusic_session.json")

class BrowserManager:
    def __init__(self, session_path: str = str(SESSION_FILE)):
        self.session_path = Path(session_path)
        self.playwright: Playwright = None
        self.context: BrowserContext = None

    def _load_session(self) -> dict:
        if self.session_path.exists():
            with open(self.session_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _save_session(self, cookies: list):
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

    def start(self):
        """启动浏览器，加载或引导登录"""
        self.playwright = sync_playwright().start()
        self.context = self.playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.session_path.parent / "chrome_data"),
            headless=False,  # 需要用户操作登录
        )
        # 尝试加载已有 cookie
        saved = self._load_session()
        if saved:
            try:
                self.context.add_cookies(saved)
            except Exception:
                pass

    def is_logged_in(self) -> bool:
        """检查 QQ 音乐是否已登录。返回 True 表示已登录。"""
        page = self.context.new_page()
        page.goto("https://y.qq.com/", timeout=15000)
        page.wait_for_timeout(2000)
        if "login" in page.url or "https://y.qq.com/" != page.url:
            page.close()
            return False
        page.close()
        return True

    def save_cookies(self):
        """持久化当前 cookies"""
        cookies = self.context.cookies()
        self._save_session(cookies)

    def get_context(self) -> BrowserContext:
        return self.context

    def close(self):
        if self.context:
            self.context.close()
        if self.playwright:
            self.playwright.stop()
