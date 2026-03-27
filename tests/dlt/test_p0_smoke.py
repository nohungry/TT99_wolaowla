"""
dlt 站點 P0 Smoke Test
每次 Release 必跑，驗證核心功能正常

對應 Node.js 版：
  tests/public.spec.js  — WIN-PUB-001~003, 007~009
  tests/auth.spec.js    — WIN-AUTH-001, 003, 005

執行方式：
    .venv/bin/pytest tests/dlt/test_p0_smoke.py -v
    .venv/bin/pytest tests/dlt/test_p0_smoke.py -m p0 -v
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.dlt.login_page import LoginPage
from pages.dlt.home_page import HomePage
from utils.locale_helper import set_locale
from utils.screenshot_helper import get_screenshotter


# ─────────────────────────────────────────────────────────────
# 登入相關
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.dlt
@pytest.mark.login
class TestLogin:
    """WIN-AUTH-001~005：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """WIN-AUTH-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """正確帳號 + 錯誤密碼應失敗，不得登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.username_input.scroll_into_view_if_needed()
        login.username_input.fill(site_config.username)
        login.password_input.scroll_into_view_if_needed()
        login.password_input.fill("wrong_password_123")
        login.login_btn.scroll_into_view_if_needed()
        login.login_btn.click()
        page.wait_for_timeout(3000)

        # 登入失敗：應停留在登入頁，不得有 LaiTsai cookie（SPA 成功跳轉後才由 JS 設定）
        expect(login.username_input).to_be_visible(timeout=5000)
        cookies = page.context.cookies()
        assert "LaiTsai" not in [c["name"] for c in cookies], \
            "錯誤密碼不應設定 LaiTsai cookie"
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_錯誤密碼_仍在登入頁")

    def test_login_wrong_username(self, page: Page, site_config):
        """不存在帳號應失敗，不得登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto_login()
        login.username_input.scroll_into_view_if_needed()
        login.username_input.fill("nonexistent_user_xyz")
        login.password_input.scroll_into_view_if_needed()
        login.password_input.fill(site_config.password)
        login.login_btn.scroll_into_view_if_needed()
        login.login_btn.click()
        page.wait_for_timeout(3000)

        # 登入失敗：應停留在登入頁，不得有 LaiTsai cookie（SPA 成功跳轉後才由 JS 設定）
        expect(login.username_input).to_be_visible(timeout=5000)
        cookies = page.context.cookies()
        assert "LaiTsai" not in [c["name"] for c in cookies], \
            "不存在帳號不應設定 LaiTsai cookie"
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_帳號不存在_仍在登入頁")

    def test_login_empty_fields(self, page: Page, site_config):
        """空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto_login()

        login.login_btn.scroll_into_view_if_needed()
        sh = get_screenshotter(page)
        if sh: sh.capture(login.login_btn, "click_送出登入_空白欄位")
        login.login_btn.click()

        # 不應跳轉，仍在登入頁
        expect(login.username_input).to_be_visible(timeout=3000)
        if sh: sh.capture(login.username_input, "verify_仍在登入頁")

    def test_login_creates_cookie(self, page: Page, site_config):
        """WIN-AUTH-003：登入後會建立主要登入 cookie（LaiTsai / userLaiTsai）"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        cookies = page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_登入後cookie狀態")

        assert "LaiTsai" in cookie_names, \
            f"找不到 LaiTsai cookie，目前 cookies：{cookie_names}"
        assert "userLaiTsai" in cookie_names, \
            f"找不到 userLaiTsai cookie，目前 cookies：{cookie_names}"

    def test_logout(self, logged_in_page: Page, site_config):
        """WIN-AUTH-005：可登出並回到未登入狀態"""
        home = HomePage(logged_in_page)
        home.logout()

        # 驗證 LaiTsai cookie 已消失
        cookies = logged_in_page.context.cookies()
        cookie_names = [c["name"] for c in cookies]
        assert "LaiTsai" not in cookie_names, \
            "登出後 LaiTsai cookie 仍存在"

        # 驗證登入按鈕重新出現
        expect(logged_in_page.get_by_role("button", name="登入")).to_be_visible()


# ─────────────────────────────────────────────────────────────
# 首頁核心（未登入）
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.dlt
@pytest.mark.home
class TestHomePage:
    """WIN-PUB-001~003, 007~009：首頁核心元素"""

    def test_home_page_loads(self, page: Page, site_config):
        """WIN-PUB-001：首頁可正常開啟"""
        login = LoginPage(page, site_config.url)
        login.goto()
        expect(page).to_have_url(re.compile(r"dev-lt\.t9platform\.com"))
        sh = get_screenshotter(page)
        if sh: sh.full_page("verify_首頁正常開啟")

    def test_navigation_visible(self, page: Page, site_config):
        """WIN-PUB-002：首頁主要分類顯示（熱門/真人/電子/捕魚）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        for label in ["熱門", "真人", "電子", "捕魚"]:
            el = page.get_by_text(label, exact=True).first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_分類_{label}")

    def test_home_category_links_exist(self, page: Page, site_config):
        """WIN-PUB-003：首頁主要分類連結存在"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        for href in ["/Categories/hot", "/Categories/casino",
                     "/Categories/slots", "/Categories/fishing"]:
            el = page.locator(f'a[href="{href}"]').first
            expect(el).to_be_visible()
            if sh: sh.capture(el, f"verify_分類連結_{href.split('/')[-1]}")

    def test_login_page_elements_exist(self, page: Page, site_config):
        """WIN-PUB-007：登入頁元素存在（帳號/密碼/送出按鈕）"""
        set_locale(page, site_config.url)
        page.goto(site_config.url.rstrip("/") + "/login")
        page.wait_for_load_state("domcontentloaded")
        sh = get_screenshotter(page)

        username_input = page.get_by_placeholder("請填寫4-10位的字母或數字")
        password_input = page.get_by_placeholder("請填寫 8-20 位的字母或數字")
        login_btn      = page.get_by_role("button", name="登入")

        expect(username_input).to_be_visible()
        expect(password_input).to_be_visible()
        expect(login_btn).to_be_visible()
        if sh: sh.capture(username_input, "verify_帳號欄位")
        if sh: sh.capture(password_input, "verify_密碼欄位")
        if sh: sh.capture(login_btn,      "verify_登入按鈕")

    def test_login_cta_navigates_to_login_page(self, page: Page, site_config):
        """WIN-PUB-009：首頁登入 CTA 可進入登入頁（登入表單出現）"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)

        login_btn = page.get_by_role("button", name="登入")
        login_btn.scroll_into_view_if_needed()
        if sh: sh.capture(login_btn, "click_登入CTA")
        # SPA pushState 不觸發 load event，改用 open_login_form 等輸入框出現
        login.open_login_form()

        expect(page.get_by_placeholder("請填寫4-10位的字母或數字")).to_be_visible()
        if sh: sh.full_page("verify_進入登入頁")


# ─────────────────────────────────────────────────────────────
# 導覽列分類頁跳轉
# ─────────────────────────────────────────────────────────────

@pytest.mark.p0
@pytest.mark.dlt
class TestNavigation:
    """WIN-PUB-008：分類頁導向"""

    @pytest.mark.parametrize("nav_item,expected_path", [
        ("熱門", "/Categories/hot"),
        ("真人", "/Categories/casino"),
        ("電子", "/Categories/slots"),
        ("捕魚", "/Categories/fishing"),
    ])
    def test_nav_to_category(self, page: Page, site_config, nav_item, expected_path):
        """WIN-PUB-008：首頁分類可導向對應頁面"""
        login = LoginPage(page, site_config.url)
        login.goto()
        sh = get_screenshotter(page)
        nav = page.get_by_text(nav_item, exact=True).first
        nav.scroll_into_view_if_needed()
        if sh: sh.capture(nav, f"click_分類_{nav_item}")
        nav.click()
        expect(page).to_have_url(re.compile(re.escape(expected_path)), timeout=8000)
        if sh: sh.full_page(f"verify_跳轉至_{nav_item}頁")
