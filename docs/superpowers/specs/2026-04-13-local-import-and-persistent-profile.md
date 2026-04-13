# 本地文件导入 & Chrome Profile 持久化

## 背景

两个独立问题需要解决：
1. 网易云音乐歌单只能获取 6 首歌（JS 动态加载，无登录态）
2. BrowserManager 每次启动创建临时 Chrome profile，状态无法跨 session 保留

## 方案 1：本地文件扫描导入歌单

### 目标
从本地音乐文件目录扫描文件名，提取歌手和歌名，替代网易云网页爬虫。

### 扫描逻辑
- 扫描目录：`E:/CloudMusic/` 和 `E:/CloudMusic/VipSongsDownload/`
- 支持文件格式：`.mp3`, `.ncm`, `.flac`, `.wav`, `.ogg`, `.m4a`, `.aac`, `.wma`
- 文件名解析规则：`Artist - Title.ext` → `Song(artist=Artist, title=Title)`
- 无法解析的文件名（不含 " - "）跳过并记录

### 界面变更（app.py）
- Step 1 区域增加"从本地目录导入"按钮
- 点击后扫描目录，显示找到的歌曲数量和前 10 首预览
- 保留原有 URL 输入方式作为备选
- 目录路径硬编码为 `E:/CloudMusic`（包含子目录 VipSongsDownload）

### 代码变更
- 新增 `crawler/local.py`：`scan_music_directory(path) -> list[Song]`
  - 递归扫描指定目录
  - 按文件扩展名过滤
  - 解析文件名为 `Song` 对象
- 修改 `app.py`：增加"从本地目录导入"按钮逻辑

## 方案 2：Chrome Profile 持久化

### 目标
使用固定路径作为 Chrome 用户数据目录，让浏览器状态（cookie、登录态等）跨 session 保持。

### 改动
- `browser/manager.py`：
  - 将 `--user-data-dir` 从 `tempfile.mkdtemp()` 改为 `data/chrome_profile`
  - 移除手动的 cookie JSON 读写逻辑（`_load_session`, `_save_session`, `SESSION_FILE`）
  - 移除 `start()` 中手动加载 cookie 的代码
  - `close()` 时只 quit driver，不删除 profile 目录
  - 处理 Chrome 锁文件冲突：如果 profile 已被占用，提示用户关闭已有 Chrome 实例
- `app.py`：移除 `save_cookies()` 调用和"检查登录状态"按钮中的 cookie 保存逻辑

### 锁文件处理
- Chrome 运行时会在 profile 目录创建 `SingletonLock` 文件
- 如果启动时检测到锁文件冲突，捕获异常并提示用户关闭已有浏览器
