import unittest
from unittest.mock import patch, MagicMock

from crawler.netease import parse_playlist_id, fetch_playlist, Song


class TestParsePlaylistId(unittest.TestCase):
    def test_from_url(self):
        assert parse_playlist_id("https://music.163.com/playlist?id=123456") == "123456"
        assert parse_playlist_id("https://music.163.com/playlist?id=98765&userid=xxx") == "98765"

    def test_plain_id(self):
        assert parse_playlist_id("123456") == "123456"

    def test_empty_string(self):
        assert parse_playlist_id("") == ""

    def test_whitespace_only(self):
        assert parse_playlist_id("   ") == ""

    def test_url_without_id_param(self):
        # 没有id参数时，返回原字符串去除首尾空白
        assert parse_playlist_id("https://music.163.com/playlist?userid=xxx") == "https://music.163.com/playlist?userid=xxx"


class TestSong(unittest.TestCase):
    def test_dataclass(self):
        s = Song(title="晴天", artist="周杰伦", album="叶惠美")
        assert s.title == "晴天"
        assert s.display_name() == "周杰伦 - 晴天"


class TestFetchPlaylist(unittest.TestCase):
    @patch("crawler.netease.requests.get")
    def test_returns_songs(self, mock_get):
        html = """
        <html><body>
        <ul class="f-hide">
            <li><a href="/song?id=1001">晴天 - 周杰伦</a></li>
            <li><a href="/song?id=1002">夜曲</a></li>
        </ul>
        </body></html>
        """
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        songs = fetch_playlist("123456", delay=0)

        assert len(songs) == 2
        assert songs[0].title == "晴天"
        assert songs[0].artist == "周杰伦"
        assert songs[1].title == "夜曲"
        assert songs[1].artist == ""

    @patch("crawler.netease.requests.get")
    def test_no_ul_returns_empty_list(self, mock_get):
        html = "<html><body><div>no list</div></body></html>"
        mock_resp = MagicMock()
        mock_resp.text = html
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        songs = fetch_playlist("123456", delay=0)

        assert songs == []

    @patch("crawler.netease.requests.get")
    def test_network_error_raises(self, mock_get):
        import requests
        mock_get.side_effect = requests.RequestException("network failure")

        with self.assertRaises(requests.RequestException):
            fetch_playlist("123456", delay=0)


if __name__ == "__main__":
    unittest.main()
