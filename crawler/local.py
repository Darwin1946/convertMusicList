"""从本地音乐文件目录扫描歌单"""

from pathlib import Path
from dataclasses import dataclass

from crawler.netease import Song

# 支持的音乐文件扩展名
MUSIC_EXTENSIONS = {".mp3", ".ncm", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma"}

# 默认扫描目录
DEFAULT_MUSIC_DIR = r"E:\CloudMusic"


def scan_music_directory(path: str = DEFAULT_MUSIC_DIR) -> list[Song]:
    """
    递归扫描目录中的音乐文件，从文件名提取歌手和歌名。

    文件名格式: "Artist - Title.ext"
    不符合此格式的文件会被跳过。

    Returns:
        歌曲列表（按文件名排序）
    """
    music_dir = Path(path)
    if not music_dir.exists():
        raise FileNotFoundError(f"目录不存在: {path}")

    songs = []
    for filepath in sorted(music_dir.rglob("*")):
        if not filepath.is_file():
            continue
        if filepath.suffix.lower() not in MUSIC_EXTENSIONS:
            continue

        # 文件名去掉扩展名
        stem = filepath.stem
        # 解析 "Artist - Title" 格式
        parts = stem.split(" - ", 1)
        if len(parts) == 2:
            artist, title = parts[0].strip(), parts[1].strip()
        else:
            # 无法解析的跳过
            continue

        if artist and title:
            songs.append(Song(title=title, artist=artist))

    return songs
