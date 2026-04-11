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

def fetch_playlist(playlist_id: str, delay: float = 1.5) -> list[Song]:
    """
    请求网易云歌单页面，解析歌曲列表。
    无需登录，但有频率限制。

    Raises:
        requests.RequestException: 如果网络请求失败。
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
        # 显示文本: "歌名 - 歌手" 或只有"歌名"
        text = a.get_text(strip=True)
        parts = text.split(" - ", 1)
        title = parts[0]
        artist = parts[1] if len(parts) > 1 else ""
        songs.append(Song(title=title, artist=artist))
        time.sleep(delay)  # 防频率限制

    return songs