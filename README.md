# 歌单转换器

将本地音乐文件批量添加到 QQ 音乐"我喜欢"歌单。

通过扫描本地音乐目录，从文件名中提取歌手和歌名，自动在 QQ 音乐搜索并收藏。

## 功能

- 扫描本地音乐目录（支持 mp3/flac/wav/ogg/m4a/aac/wma/ncm）
- 自动解析 `歌手 - 歌名` 格式的文件名
- Chrome 浏览器自动化操作 QQ 音乐
- 登录状态持久化，无需重复登录
- 批量搜索并收藏歌曲，自动跳过已收藏

## 安装

```bash
pip install -r requirements.txt
pip install selenium webdriver-manager
```

需要安装 [Chrome 浏览器](https://www.google.com/chrome/) 和对应版本的 ChromeDriver。

## 使用

```bash
streamlit run app.py
```

1. 输入音乐目录路径，点击"扫描本地音乐文件"
2. 点击"启动浏览器"，在弹出窗口中登录 QQ 音乐
3. 点击"检查登录状态"确认已登录
4. 点击"开始添加歌曲"，等待批量完成

## 项目结构

```
app.py                  # Streamlit 主界面
crawler/
  local.py              # 本地音乐文件扫描
  netease.py            # 网易云音乐歌单解析（备用）
browser/
  manager.py            # Chrome 浏览器管理
  qqmusic.py            # QQ 音乐搜索与收藏操作
```
