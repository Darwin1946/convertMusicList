from dataclasses import dataclass
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import selenium.common.exceptions
import time
import re


@dataclass
class SongMatch:
    song_id: str  # 歌曲 mid (如 "0014qLXa1JrJ11")
    title: str
    singer: str

    def display(self) -> str:
        return f"{self.singer} - {self.title}"


def get_user_playlists(driver: webdriver.Chrome) -> list[dict]:
    """
    访问 QQ 音乐歌单列表页面，解析用户歌单列表。
    返回 [{id, name, song_count}, ...]
    """
    driver.get("https://y.qq.com/portal/playlist.html")
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, ".playlist__item"))
    )
    time.sleep(2)

    playlists = []
    items = driver.find_elements(By.CSS_SELECTOR, ".playlist__item")

    for item in items:
        links = item.find_elements(By.CSS_SELECTOR, "a[href*='/playlist/']")
        playlist_id = None
        playlist_url = None
        for link in links:
            href = link.get_attribute("href") or ""
            m = re.search(r'/playlist/(\d+)', href)
            if m and "like" not in href:
                playlist_id = m.group(1)
                playlist_url = href
                break

        if not playlist_id:
            continue

        try:
            title_el = item.find_element(By.CSS_SELECTOR, ".playlist__title_txt")
            name = title_el.text.strip()
        except selenium.common.exceptions.NoSuchElementException:
            try:
                name = item.get_attribute("title") or item.text.split("\n")[0]
            except:
                name = ""

        playlists.append({
            "id": playlist_id,
            "name": name,
            "url": playlist_url
        })

    return playlists


def search_song(driver: webdriver.Chrome, keyword: str) -> Optional[SongMatch]:
    """
    在 QQ 音乐搜索页面搜索歌曲，返回第一个精确匹配结果。
    keyword 格式: "歌手 歌名"
    """
    keyword = keyword.strip()
    encoded = keyword.replace(" ", "%20")

    driver.get(f"https://y.qq.com/n/ryqq_v2/search?w={encoded}&t=song&remoteplace=txt.yqq.center")
    time.sleep(3)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".songlist__item"))
        )
    except selenium.common.exceptions.TimeoutException:
        return None

    items = driver.find_elements(By.CSS_SELECTOR, ".songlist__item")

    for item in items:
        try:
            name_el = item.find_element(By.CSS_SELECTOR, ".songlist__songname_txt a")
            title = name_el.text.strip()
            href = name_el.get_attribute("href") or ""

            try:
                singer_el = item.find_element(By.CSS_SELECTOR, ".songlist__artist")
                singer = singer_el.text.strip()
            except:
                singer = ""

            m = re.search(r'/songDetail/([A-Za-z0-9]+)', href)
            if m:
                song_id = m.group(1)
            else:
                song_id = ""

            if title and song_id:
                return SongMatch(song_id=song_id, title=title, singer=singer)
        except:
            continue

    return None


def add_song_to_playlist(driver: webdriver.Chrome, song_id: str, playlist_id: str) -> bool:
    """
    将指定歌曲收藏到"我喜欢"歌单。

    流程: 歌曲详情页 -> 点击"收藏"按钮
    如果已收藏则跳过
    playlist_id 参数保留但不使用（收藏直接到"我喜欢"）
    """
    song_url = f"https://y.qq.com/n/ryqq_v2/songDetail/{song_id}"
    driver.get(song_url)

    # 等待页面加载
    time.sleep(5)

    # 滚动到页面顶部
    driver.execute_script("window.scrollTo(0, 0);")
    time.sleep(1)

    # 查找收藏按钮 - 是一个 span.btn__txt 元素
    collect_btn = None
    all_spans = driver.find_elements(By.CSS_SELECTOR, "span.btn__txt")
    for span in all_spans:
        try:
            if span.is_displayed():
                txt = span.text.strip()
                loc = span.location
                if txt == "收藏" and loc['y'] < 400:  # 在页面顶部附近
                    collect_btn = span
                    print(f"找到收藏按钮 at y={loc['y']}: {txt!r}")
                    break
        except:
            pass

    if not collect_btn:
        # 如果找不到"收藏"按钮，说明可能已经收藏了
        # 或者按钮已经变成"已收藏"
        print("未找到收藏按钮，可能已收藏，跳过")
        return True

    btn_text = collect_btn.text.strip()
    print(f"收藏按钮: {btn_text!r}")

    # 如果已经显示"已收藏"则跳过（点击会取消收藏）
    # 按钮文字：未收藏显示"收藏"，已收藏显示"已收藏"
    if btn_text == "已收藏" or btn_text == "已喜欢":
        print("歌曲已经收藏过，跳过")
        return True

    # 否则点击收藏
    try:
        driver.execute_script("arguments[0].click();", collect_btn)
        print("已点击收藏按钮")
    except Exception as e:
        print(f"点击收藏按钮失败: {e}")
        return False

    # 等待弹窗显示并自动消失
    time.sleep(4)
    return True


def get_song_ids_from_playlist(driver: webdriver.Chrome, playlist_id: str) -> list[str]:
    """从歌单详情页提取所有歌曲的 ID (mid) 列表。"""
    playlist_url = f"https://y.qq.com/n/ryqq/playlist/{playlist_id}"
    driver.get(playlist_url)
    time.sleep(3)

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".songlist__item"))
        )
    except selenium.common.exceptions.TimeoutException:
        return []

    song_ids = []
    items = driver.find_elements(By.CSS_SELECTOR, ".songlist__item")

    for item in items:
        try:
            name_el = item.find_element(By.CSS_SELECTOR, ".songlist__songname_txt a")
            href = name_el.get_attribute("href") or ""
            m = re.search(r'/songDetail/([A-Za-z0-9]+)', href)
            if m:
                song_ids.append(m.group(1))
        except:
            continue

    return song_ids
