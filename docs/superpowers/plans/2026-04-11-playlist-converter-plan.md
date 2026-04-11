# 歌单转换器实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 用户输入网易云歌单链接，工具自动将歌曲批量添加到 QQ 音乐已有歌单中。

**Architecture:** Streamlit 单页应用 + Playwright 浏览器自动化。网易云歌单通过 requests 解析；QQ 音乐操作通过 Playwright 控制已登录浏览器完成。

**Tech Stack:** Python 3.10+, Streamlit, Playwright, requests, BeautifulSoup

---

## 文件结构

```
convertMusic/
├── app.py                      # Streamlit 主应用入口
├── requirements.txt            # 依赖列表
├── .gitignore                  #忽略 data/ 目录
├── crawler/
│   └── netease.py              # 网易云歌单解析
├── browser/
│   ├── manager.py              # Playwright session 管理（cookie 持久化）
│   └── qqmusic.py               # QQ 音乐页面操作（获取歌单、搜索、添加）
├── data/                        # Playwright session 文件存放目录
│   └── .gitkeep
└── docs/
    └── superpowers/
        ├── specs/
        │   └── 2026-04-11-playlist-converter-design.md
        └── plans/
            └── 2026-04-11-playlist-converter-plan.md
```

---

## Task 1: 项目初始化

**Files:**
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `data/.gitkeep`
- Create: `crawler/__init__.py`
- Create: `browser/__init__.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
streamlit>=1.28.0
playwright>=1.40.0
requests>=2.31.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

- [ ] **Step 2: 创建 .gitignore**

```gitignore
data/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: 创建目录结构和空 `__init__.py` 文件**

```bash
mkdir -p crawler browser data docs/superpowers/specs docs/superpowers/plans
touch crawler/__init__.py browser/__init__.py data/.gitkeep
```

---

## Task 2: 网易云歌单解析器

**Files:**
- Create: `crawler/netease.py`
- Test: `tests/crawler/test_netease.py`

- [ ] **Step 1: 写测试用例**

创建 `tests/crawler/test_netease.py`（先建目录）：

```python
# tests/crawler/__init__.py 也需要创建

def test_parse_playlist_id_from_url():
    from crawler.netease import parse_playlist_id
    assert parse_playlist_id("https://music.163.com/playlist?id=123456") == "123456"
    assert parse_playlist_id("https://music.163.com/playlist?id=98765&userid=xxx") == "98765"
    assert parse_playlist_id("123456") == "123456"

def test_song_dataclass():
    from crawler.netease import Song
    s = Song(title="晴天", artist="周杰伦", album="叶惠美")
    assert s.title == "晴天"
    assert s.display_name() == "周杰伦 - 晴天"
```

- [ ] **Step 2: 运行测试，验证失败（函数不存在）**

```bash
pytest tests/crawler/test_netease.py -v
# 预期: FAIL — import error 或 function not found
```

- [ ] **Step 3: 实现 crawler/netease.py**

```python
from dataclasses import dataclass
import re
import requests
from bs4 import BeautifulSoup
import time

@dataclass
class Song:
    title: str
    artist: str
    album: str = ""

    def display_name(self) -> str:
        return f"{self.artist} - {self.title}"

def parse_playlist_id(url_or_id: str) -> str:
    match = re.search(r'[?&]id=(\d+)', url_or_id)
    if match:
        return match.group(1)
    return url_or_id.strip()

def fetch_playlist(playlist_id: str) -> list[Song]:
    """
    请求网易云歌单页面，解析歌曲列表。
    无需登录，但有频率限制。
    """
    url = f"https://music.163.com/playlist?id={playlist_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://music.163.com/",
    }
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    songs = []
    # 歌曲列表在 <ul class="f-hide"> 下的 <li><a href="/song?id=xxx">歌名 - 歌手</a></li>
    ul = soup.find("ul", class_="f-hide")
    if not ul:
        return songs

    for a in ul.find_all("a"):
        href = a.get("href", "")
        # href 格式: /song?id=1234567
        mid = re.search(r'/song\?id=(\d+)', href)
        # 显示文本: "歌名 - 歌手" 或只有"歌名"
        text = a.get_text(strip=True)
        parts = text.split(" - ", 1)
        title = parts[0]
        artist = parts[1] if len(parts) > 1 else ""
        songs.append(Song(title=title, artist=artist))
        time.sleep(1.5)  # 防频率限制

    return songs
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/crawler/test_netease.py -v
# 预期: PASS
```

---

## Task 3: Playwright 浏览器管理器

**Files:**
- Create: `browser/manager.py`
- Test: `tests/browser/test_manager.py`

- [ ] **Step 1: 写测试用例（测试 session 文件不存在的情况）**

```python
# tests/browser/__init__.py 也需要创建

def test_session_file_not_exists():
    from browser.manager import BrowserManager
    bm = BrowserManager(session_path="data/nonexistent.json")
    # 初始状态应为未登录
    assert not bm.is_logged_in()
```

- [ ] **Step 2: 运行测试验证失败**

```bash
pytest tests/browser/test_manager.py -v
# 预期: FAIL
```

- [ ] **Step 3: 实现 browser/manager.py**

```python
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

    def ensure_logged_in(self) -> bool:
        """检查 QQ 音乐是否已登录。返回 True 表示已登录。"""
        page = self.context.new_page()
        page.goto("https://y.qq.com/", timeout=15000)
        # 检查登录区域是否存在（未登录会有登录按钮）
        page.wait_for_timeout(2000)
        # 简单判断：检查页面是否跳转到登录页
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
```

- [ ] **Step 4: 运行测试验证通过**

```bash
pytest tests/browser/test_manager.py -v
# 预期: PASS
```

---

## Task 4: QQ 音乐页面操作

**Files:**
- Create: `browser/qqmusic.py`
- Test: `tests/browser/test_qqmusic.py`

- [ ] **Step 1: 写测试用例（测试 SongMatch 数据类）**

```python
# tests/browser/__init__.py 也需要创建

def test_song_match():
    from browser.qqmusic import SongMatch
    m = SongMatch(song_id="123", title="晴天", singer="周杰伦")
    assert m.title == "晴天"
    assert m.display() == "周杰伦 - 晴天"
```

- [ ] **Step 2: 实现 browser/qqmusic.py**

```python
from dataclasses import dataclass

@dataclass
class SongMatch:
    song_id: str
    title: str
    singer: str

    def display(self) -> str:
        return f"{self.singer} - {self.title}"

def get_user_playlists(context) -> list[dict]:
    """
    访问 QQ 音乐个人主页，解析用户歌单列表。
    返回 [{id, name, song_count}, ...]
    """
    page = context.new_page()
    page.goto("https://y.qq.com/portal/profile.html", timeout=15000)
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(2000)

    playlists = []
    # TODO: 实际需要分析 QQ 音乐页面 DOM 结构后填写选择器
    # 临时返回空列表占位，等待后续 DOM 分析
    page.close()
    return playlists

def search_song(context, keyword: str) -> SongMatch | None:
    """
    在 QQ 音乐搜索页面搜索歌曲，返回第一个精确匹配结果。
    keyword 格式: "歌手 歌名"
    """
    page = context.new_page()
    search_url = f"https://y.qq.com/portal/search.html?w={keyword}&remoteplace=txt.yqq.top"
    page.goto(search_url, timeout=15000)
    page.wait_for_load_state("networkidle", timeout=10000)
    page.wait_for_timeout(2000)

    # TODO: 实际需要分析 DOM 选择器后填写
    # 临时返回 None 占位
    page.close()
    return None

def add_song_to_playlist(context, song_id: str, playlist_id: str) -> bool:
    """
    将指定歌曲添加到指定歌单。
    方式：在歌曲搜索结果页点击"添加到歌单"按钮。
    """
    page = context.new_page()
    # TODO: 分析 QQ 音乐"添加到歌单"弹窗的 DOM 操作流程
    page.close()
    return False
```

- [ ] **Step 3: 运行测试验证通过**

```bash
pytest tests/browser/test_qqmusic.py -v
# 预期: PASS
```

**注意:** Task 4 中 `get_playlists`、`search_song`、`add_song_to_playlist` 的 DOM 选择器需要后续在浏览器中手动分析 QQ 音乐页面后填写。目前先完成函数签名和基本逻辑。

---

## Task 5: Streamlit 主应用

**Files:**
- Create: `app.py`
- Test: `tests/test_app.py`（可选，Streamlit 测试较复杂）

- [ ] **Step 1: 实现 app.py**

```python
import streamlit as st
from crawler.netease import parse_playlist_id, fetch_playlist, Song
from browser.manager import BrowserManager
from browser import qqmusic

# 页面配置
st.set_page_config(page_title="歌单转换器", page_icon="🎵")
st.title("🎵 歌单转换器")
st.markdown("将网易云音乐歌单批量添加到 QQ 音乐")

# 初始化 session state
if "songs" not in st.session_state:
    st.session_state.songs = []
if "bm" not in st.session_state:
    st.session_state.bm = None
if "playlists" not in st.session_state:
    st.session_state.playlists = []
if "target_playlist" not in st.session_state:
    st.session_state.target_playlist = None

# Step 1: 输入网易云歌单
st.header("Step 1: 输入网易云歌单链接")
url_input = st.text_input("歌单链接", placeholder="https://music.163.com/playlist?id=...")
if url_input:
    pid = parse_playlist_id(url_input)
    st.info(f"解析到歌单 ID: {pid}")
    if st.button("获取歌曲列表"):
        with st.spinner("正在获取歌曲列表..."):
            songs = fetch_playlist(pid)
        st.session_state.songs = songs
        st.success(f"获取到 {len(songs)} 首歌曲")

if st.session_state.songs:
    st.write(f"歌曲列表（前10首）:")
    for s in st.session_state.songs[:10]:
        st.write(f"  - {s.display_name()}")
    if len(st.session_state.songs) > 10:
        st.write(f"  ... 还有 {len(st.session_state.songs) - 10} 首")

# Step 2: 登录 QQ 音乐
st.header("Step 2: 登录 QQ 音乐")
if st.button("启动浏览器（首次需要扫码/账号登录）"):
    bm = BrowserManager()
    bm.start()
    st.session_state.bm = bm
    st.info("请在打开的浏览器中完成 QQ 音乐登录")

if st.session_state.bm:
    bm = st.session_state.bm
    if bm.ensure_logged_in():
        st.success("✅ 已登录 QQ 音乐")
        bm.save_cookies()
        # 获取歌单列表
        playlists = qqmusic.get_user_playlists(bm.get_context())
        st.session_state.playlists = playlists
    else:
        st.warning("⚠️ 请在浏览器中完成登录后点击下方按钮")

# Step 3: 选择目标歌单
if st.session_state.playlists:
    st.header("Step 3: 选择目标歌单")
    playlist_names = [p["name"] for p in st.session_state.playlists]
    selected = st.selectbox("选择 QQ 音乐目标歌单", playlist_names)
    st.session_state.target_playlist = selected

# Step 4: 开始转换
if st.session_state.songs and st.session_state.target_playlist and st.session_state.bm:
    st.header("Step 4: 开始转换")
    target_id = next(
        p["id"] for p in st.session_state.playlists
        if p["name"] == st.session_state.target_playlist
    )
    if st.button("🚀 开始添加歌曲"):
        progress = st.progress(0)
        status = st.empty()
        results = {"success": 0, "failed": 0, "failed_songs": []}

        for i, song in enumerate(st.session_state.songs):
            status.text(f"正在处理: {song.display_name()} ({i+1}/{len(st.session_state.songs)})")
            match = qqmusic.search_song(st.session_state.bm.get_context(), song.display_name())
            if match:
                ok = qqmusic.add_song_to_playlist(st.session_state.bm.get_context(), match.song_id, target_id)
                if ok:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["failed_songs"].append(song)
            else:
                results["failed"] += 1
                results["failed_songs"].append(song)
            progress.progress((i + 1) / len(st.session_state.songs))

        st.success(f"完成！成功 {results['success']} 首，失败 {results['failed']} 首")
        if results["failed_songs"]:
            st.write("失败歌曲:")
            for s in results["failed_songs"]:
                st.write(f"  - {s.display_name()}")
```

---

## 执行顺序

1. Task 1（项目初始化）
2. Task 2（网易云解析器）— 可独立测试
3. Task 3（Playwright 管理器）— 可独立测试
4. Task 4（QQ 音乐操作）— DOM 选择器需后续填充
5. Task 5（Streamlit 应用）— 串联全部模块

**Plan complete.** 保存于 `docs/superpowers/plans/2026-04-11-playlist-converter-plan.md`。

两种执行方案：

**1. Subagent-Driven（推荐）** — 每个 Task 由独立 subagent 完成，任务间有检查点

**2. Inline Execution** — 在当前 session 中逐步执行，批量处理后检查

你选哪个？