# tests/browser/test_qqmusic.py

def test_song_match():
    from browser.qqmusic import SongMatch
    m = SongMatch(song_id="123", title="晴天", singer="周杰伦")
    assert m.title == "晴天"
    assert m.display() == "周杰伦 - 晴天"
