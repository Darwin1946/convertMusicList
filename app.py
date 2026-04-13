import streamlit as st
import time
from crawler.netease import Song
from crawler.local import scan_music_directory
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

# Step 1: 输入歌单
st.header("Step 1: 获取歌曲列表")

if st.button("扫描本地音乐文件"):
    with st.spinner("正在扫描..."):
        try:
            songs = scan_music_directory()
            if not songs:
                st.warning("未找到音乐文件")
            else:
                st.session_state.songs = songs
                st.success(f"找到 {len(songs)} 首歌曲")
        except FileNotFoundError as e:
            st.error(str(e))

if st.session_state.songs:
    st.write(f"歌曲列表（前10首）:")
    for s in st.session_state.songs[:10]:
        st.write(f"  - {s.display_name()}")
    if len(st.session_state.songs) > 10:
        st.write(f"  ... 还有 {len(st.session_state.songs) - 10} 首")

# Step 2: 登录 QQ 音乐
st.header("Step 2: 登录 QQ 音乐")
if st.button("启动浏览器（首次需要扫码/账号登录）"):
    try:
        bm = BrowserManager()
        bm.start()
        st.session_state.bm = bm
        st.info("请在打开的浏览器中完成 QQ 音乐登录")
    except Exception as e:
        st.error(f"启动浏览器失败: {e}")
        if "lock" in str(e).lower() or "profile" in str(e).lower():
            st.warning("请先关闭其他使用同一 Chrome profile 的浏览器窗口")

if st.session_state.bm:
    bm = st.session_state.bm
    if st.button("检查登录状态"):
        if bm.is_logged_in():
            st.success("✅ 已登录 QQ 音乐")
        else:
            st.warning("⚠️ 请在浏览器中完成登录后点击下方按钮")

# Step 3: 开始转换
if st.session_state.songs and st.session_state.bm:
    st.header("Step 3: 开始转换")
    if st.button("🚀 开始添加歌曲"):
        progress = st.progress(0)
        status = st.empty()
        results = {"success": 0, "failed": 0, "failed_songs": []}

        for i, song in enumerate(st.session_state.songs):
            status.text(f"正在处理: {song.display_name()} ({i+1}/{len(st.session_state.songs)})")
            match = qqmusic.search_song(st.session_state.bm.get_driver(), song.display_name())
            if match:
                ok = qqmusic.add_song_to_playlist(st.session_state.bm.get_driver(), match.song_id, "")
                if ok:
                    results["success"] += 1
                else:
                    results["failed"] += 1
                    results["failed_songs"].append(song)
            else:
                results["failed"] += 1
                results["failed_songs"].append(song)
            progress.progress((i + 1) / len(st.session_state.songs))
            time.sleep(1)  # 每首歌处理后等待1秒，避免请求过快

        st.success(f"完成！成功 {results['success']} 首，失败 {results['failed']} 首")
        if results["failed_songs"]:
            st.write("失败歌曲:")
            for s in results["failed_songs"]:
                st.write(f"  - {s.display_name()}")
        st.stop()
