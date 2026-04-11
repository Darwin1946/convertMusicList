# 歌单转换器设计文档

## 项目概述

将网易云音乐歌单中的歌曲批量添加到 QQ 音乐歌单中。

## 技术栈

- **前端**：Streamlit（Python Web 框架）
- **浏览器自动化**：Playwright（持久化 session）
- **爬虫**：requests + BeautifulSoup（网易云）
- **语言**：Python 3.10+

## 架构

```
┌──────────────────────────────────────────────────────────┐
│                    Streamlit Web App                     │
│                                                          │
│  Step 1: 输入网易云歌单链接                               │
│          ↓                                               │
│  Step 2: 解析歌单歌曲列表（歌名 + 歌手）                   │
│          ↓                                               │
│  Step 3: 启动 Playwright 浏览器                          │
│          用户手动登录 QQ 音乐（一次性）                    │
│          ↓                                               │
│  Step 4: 获取用户 QQ 音乐已有歌单列表                     │
│          用户选择目标歌单                                 │
│          ↓                                               │
│  Step 5: 遍历歌曲，在 QQ 音乐 搜索并添加                   │
│          显示进度条                                       │
└──────────────────────────────────────────────────────────┘
```

## 核心模块

### 1. 网易云歌单解析器 (`crawler/netease.py`)

- 输入：网易云歌单 URL 或 ID
- 输出：`List[Song]`，Song 包含 `{title, artist, album}`
- 方式：请求 `https://music.163.com/playlist?id={id}`，解析 HTML
- 防限：请求间隔 1.5 秒

### 2. 浏览器管理器 (`browser/manager.py`)

- 持久化 Playwright Context（cookie 保存到 `data/qqmusic_session.json`）
- 首次启动时让用户登录 QQ 音乐，之后复用 session
- 提供方法：
  - `ensure_logged_in()` — 检查登录状态，未登录则引导
  - `get_playlists()` — 获取用户歌单列表
  - `add_song_to_playlist(song, playlist_id)` — 添加歌曲到指定歌单

### 3. QQ 音乐操作 (`browser/qqmusic.py`)

- 访问 `https://y.qq.com/portal/profile.html` 解析歌单列表
- 搜索歌曲：`https://y.qq.com/portal/search.html`，取精确匹配的第一个结果
- 添加方式：搜索结果点击"添加到歌单"按钮

### 4. Streamlit 前端 (`app.py`)

- 页面：单页应用，分步引导
- 状态： Streamlit `session_state` 管理登录状态、歌曲列表、进度

## 数据流

```
网易云 URL → 解析歌曲列表 → [User] 登录 QQ 音乐（首次）→
获取已有歌单 → 用户选择目标歌单 → 逐个添加歌曲 → 完成
```

## 关键决策

1. **歌曲匹配**：搜索"歌名 歌手"，取第一个结果；若无匹配结果标记为失败
2. **添加失败处理**：单个歌曲失败不影响其他，继续处理并在最后展示失败列表
3. **进度展示**：Streamlit 进度条 + 实时日志
4. **中断支持**：提供"停止"按钮，设置全局 flag 停止添加循环

## 项目结构

```
convertMusic/
├── app.py                  # Streamlit 主应用
├── crawler/
│   └── netease.py          # 网易云歌单解析
├── browser/
│   ├── manager.py          # Playwright session 管理
│   └── qqmusic.py          # QQ 音乐页面操作
├── data/
│   └── qqmusic_session.json  # 持久化 cookies（gitignore）
├── requirements.txt
└── docs/
    └── specs/
        └── 2026-04-11-playlist-converter-design.md
```

## 风险与应对

| 风险 | 应对 |
|------|------|
| 网易云接口被限 | 请求间隔 1.5 秒 + User-Agent 轮换 |
| QQ 音乐 UI 改版 | DOM 选择器失效时更新 `qqmusic.py` 中的选择器 |
| 歌单歌曲过多耗时 | 进度条 + 预估时间，用户可随时中断 |
