"""
pytest 全域設定
- 讀取 --site 參數
- 提供 site_config / page / logged_in_page fixture
- 每個測試結束後自動登出
"""

import os
import time
import pytest
from playwright.sync_api import Page, Playwright
from config.settings import get_site_config
from pages.login_page import LoginPage
from pages.home_page import HomePage

@pytest.fixture(scope="session")
def browser(playwright: Playwright):
    """透過 CDP 連接已開啟的 Windows Chrome（CDP_URL 從 .env 讀取）"""
    cdp_url = os.getenv("CDP_URL", "http://localhost:9222")
    browser = playwright.chromium.connect_over_cdp(cdp_url)
    yield browser
    # 不關閉 browser，避免把 Windows Chrome 一起關掉


@pytest.fixture(scope="function")
def page(browser):
    """每個測試建立獨立 context，視窗最大化"""
    context = browser.new_context(no_viewport=True)
    page = context.new_page()
    # 透過 CDP 指令將視窗最大化
    cdp = context.new_cdp_session(page)
    window_id = cdp.send("Browser.getWindowForTarget")["windowId"]
    cdp.send("Browser.setWindowBounds", {
        "windowId": window_id,
        "bounds": {"windowState": "maximized"},
    })
    cdp.detach()
    # 注入 MutationObserver：偵測到「伺服器錯誤」彈窗時自動點確定
    page.add_init_script("""
        new MutationObserver(() => {
            const btn = document.querySelector('button.toast-confirm-btn');
            if (btn && btn.offsetParent !== null) btn.click();
        }).observe(document.body, { childList: true, subtree: true });
    """)
    yield page
    context.close()


# -----------------------------------------------
# 新增 --site 命令列參數
# -----------------------------------------------
def pytest_addoption(parser):
    parser.addoption(
        "--site",
        action="store",
        default=None,
        help="指定測試站點，例如：--site=wlj",
    )


# -----------------------------------------------
# 每個測試結束後：嘗試登出，再等 3 秒
# -----------------------------------------------
@pytest.fixture(autouse=True)
def auto_logout_after_test(page: Page):
    yield
    try:
        home = HomePage(page)
        # 如果頭像存在代表還在登入狀態，執行登出
        if home.avatar.is_visible(timeout=2000):
            home.logout()
    except Exception:
        pass  # 未登入或已登出，略過
    time.sleep(3)


# -----------------------------------------------
# Fixtures
# -----------------------------------------------
@pytest.fixture(scope="session")
def site_config(request):
    """讀取站點設定（整個 session 共用）"""
    site_id = request.config.getoption("--site")
    return get_site_config(site_id)


@pytest.fixture(scope="function")
def login_page(page: Page, site_config):
    """提供 LoginPage 實例"""
    return LoginPage(page, site_config.url)


@pytest.fixture(scope="function")
def logged_in_page(page: Page, site_config):
    """
    已登入狀態的 fixture
    測試需要登入後才能執行的功能時使用這個
    """
    login = LoginPage(page, site_config.url)
    login.goto_and_login(site_config.username, site_config.password)

    home = HomePage(page)
    home.verify_login_success(site_config.username)
    home.dismiss_any_popups()

    return page
