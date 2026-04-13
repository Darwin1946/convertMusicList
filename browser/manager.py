import os
import sys
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

# Use cached chromedriver to avoid version issues
CHROMEDRIVER_PATH = "C:/Users/tangy/.wdm/drivers/chromedriver/win64/147.0.7727.56/chromedriver-win32/chromedriver.exe"

CHROME_BINARY = os.environ.get("CHROME_BINARY", "C:/Program Files/Google/Chrome/Application/chrome.exe")
CHROME_PROFILE_DIR = Path("data/chrome_profile")


class BrowserManager:
    def __init__(self):
        self.driver: webdriver.Chrome = None

    def start(self, headless: bool = False):
        """启动 Chrome 浏览器，使用持久化 profile 保持登录态"""
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.binary_location = CHROME_BINARY
        # 禁用自动化标志，避免被检测
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        # 沙盒参数，避免 Chrome 崩溃
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        # 持久化用户数据目录（Cookie 和登录状态跨 session 保留）
        CHROME_PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        options.add_argument(f"--user-data-dir={CHROME_PROFILE_DIR.resolve()}")

        self.driver = webdriver.Chrome(service=Service(CHROMEDRIVER_PATH), options=options)

        # 禁用 webdriver 属性
        self.driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        # 立即打开 QQ 音乐
        self.driver.get("https://y.qq.com/")

    def is_logged_in(self) -> bool:
        """检查 QQ 音乐是否已登录。返回 True 表示已登录。"""
        if self.driver is None:
            return False
        try:
            self.driver.get("https://y.qq.com/")
            # 等待页面加载
            self.driver.implicitly_wait(3)
            # 检查 URL 是否跳转到登录页
            current_url = self.driver.current_url
            if "login" in current_url:
                return False
            if current_url == "https://y.qq.com/" or current_url.startswith("https://y.qq.com"):
                return True
            return False
        except Exception:
            return False

    def get_driver(self) -> webdriver.Chrome:
        return self.driver

    def close(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
