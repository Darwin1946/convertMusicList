# tests/browser/__init__.py also needs to be created

def test_session_file_not_exists():
    from browser.manager import BrowserManager
    bm = BrowserManager(session_path="data/nonexistent.json")
    # Initial state should be not logged in
    assert not bm.is_logged_in()
