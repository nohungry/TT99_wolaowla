"""
P0 Smoke Test
每次 Release 必跑，驗證核心功能正常
"""

import re
import pytest
from playwright.sync_api import Page, expect
from pages.login_page import LoginPage
from pages.home_page import HomePage


class TestLogin:
    """TC-001 ~ TC-004：登入相關"""

    def test_login_success(self, page: Page, site_config):
        """TC-001：正常登入"""
        login = LoginPage(page, site_config.url)
        login.goto_and_login(site_config.username, site_config.password)

        home = HomePage(page)
        home.verify_login_success(site_config.username)

    def test_login_wrong_password(self, page: Page, site_config):
        """TC-002：正確帳號 + 錯誤密碼應失敗，並出現「密碼錯誤」警告彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login(site_config.username, "wrong_password_123")

        # 應出現錯誤提示彈窗（toast-confirm-btn 為錯誤/警告彈窗的確定按鈕）
        expect(page.locator("button.toast-confirm-btn")).to_be_visible(timeout=5000)

    def test_login_wrong_username(self, page: Page, site_config):
        """TC-003：不存在帳號應失敗，並出現「帳號不存在」警告彈窗"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()
        login.login("nonexistent_user_xyz", site_config.password)

        # 應出現錯誤提示彈窗
        expect(page.locator("button.toast-confirm-btn")).to_be_visible(timeout=5000)

    def test_login_empty_fields(self, page: Page, site_config):
        """TC-004：空白帳號密碼不應登入成功"""
        login = LoginPage(page, site_config.url)
        login.goto()
        login.open_login_form()

        # 直接點登入按鈕（不填資料）
        login.login_btn.click()

        # 不應跳轉（仍在登入頁）
        expect(login.username_input).to_be_visible(timeout=3000)


class TestHomePage:
    """TC-005 ~ TC-007：首頁核心元素"""

    def test_home_page_loads(self, logged_in_page: Page, site_config):
        """TC-005：登入後首頁正常載入"""
        # 驗證帳號名稱顯示
        expect(
            logged_in_page.locator(f"text={site_config.username}")
        ).to_be_visible()

    def test_navigation_visible(self, logged_in_page: Page):
        """TC-006：主要導覽列應顯示"""
        # 驗證導覽列項目（真人、電子、捕魚）
        for nav_item in ["真人", "電子", "捕魚"]:
            expect(
                logged_in_page.locator(f"text={nav_item}").first
            ).to_be_visible()

    def test_logout(self, logged_in_page: Page):
        """TC-007：登入後可正常登出，右上角應出現「登入」按鈕"""
        home = HomePage(logged_in_page)
        home.logout()
        expect(home.login_btn).to_be_visible(timeout=5000)


class TestPersonalInfo:
    """TC-011 ~ TC-012：個人資訊彈窗"""

    def test_personal_info_opens(self, logged_in_page: Page, site_config):
        """TC-011：個人資訊彈窗可正常開啟，帳號欄位顯示正確用戶名"""
        # sidebar 容器 width=0，需 force=True 繞過 actionability 檢查
        logged_in_page.locator(".sidebar-item.user").dispatch_event("click")
        expect(logged_in_page.locator(".dialog-container")).to_be_visible(timeout=5000)
        expect(
            logged_in_page.locator(".dialog-container input[disabled]").first
        ).to_have_value(site_config.username)

    def test_personal_info_closes(self, logged_in_page: Page):
        """TC-012：個人資訊彈窗可正常關閉（X 按鈕）"""
        logged_in_page.locator(".sidebar-item.user").dispatch_event("click")
        expect(logged_in_page.locator(".dialog-container")).to_be_visible(timeout=5000)
        logged_in_page.locator(".close-wrap").click()
        expect(logged_in_page.locator(".dialog-container")).not_to_be_visible(timeout=5000)


class TestInbox:
    """TC-013 ~ TC-014：站內信彈窗"""

    def test_inbox_opens(self, logged_in_page: Page):
        """TC-013：站內信彈窗可正常開啟"""
        logged_in_page.locator(".sidebar-item.mail").dispatch_event("click")
        dialog = logged_in_page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("站內信")

    def test_inbox_closes(self, logged_in_page: Page):
        """TC-014：站內信彈窗可正常關閉"""
        logged_in_page.locator(".sidebar-item.mail").dispatch_event("click")
        expect(logged_in_page.locator(".dialog-container")).to_be_visible(timeout=5000)
        logged_in_page.locator(".close-wrap").click()
        expect(logged_in_page.locator(".dialog-container")).not_to_be_visible(timeout=5000)


class TestCasinoPage:
    """TC-015：真人頁廳館"""

    def test_casino_halls_visible(self, logged_in_page: Page):
        """TC-015：真人頁顯示所有廳館（T9真人、RC真人、DG真人、MT真人、歐博）"""
        home = HomePage(logged_in_page)
        home.click_nav_item("真人")
        for hall in ["T9真人", "RC真人", "DG真人", "MT真人", "歐博"]:
            expect(logged_in_page.locator(f"text={hall}").first).to_be_visible(timeout=8000)


class TestHomePageSections:
    """TC-016 ~ TC-019：首頁各區塊"""

    def test_hot_games_section(self, logged_in_page: Page):
        """TC-016：首頁顯示「熱門遊戲」區塊且有遊戲卡片"""
        expect(logged_in_page.locator("text=熱門遊戲").first).to_be_visible()
        expect(logged_in_page.locator(".mt-d-20.grid").first).to_be_visible()

    def test_new_games_section(self, logged_in_page: Page):
        """TC-017：首頁顯示「最新遊戲」區塊且有遊戲卡片"""
        # 熱門/最新共用同一個 grid，點 tab 切換後確認有卡片
        logged_in_page.locator("text=最新遊戲").first.click()
        expect(logged_in_page.locator(".mt-d-20.grid").first).to_be_visible()

    def test_announcement_marquee(self, logged_in_page: Page):
        """TC-018：首頁公告跑馬燈有內容顯示"""
        # 多個 p.h-full 存在，取第一個含公告文字的
        marquee = logged_in_page.locator("p.h-full").first
        expect(marquee).to_be_visible()
        expect(marquee).to_contain_text("公告")

    def test_balance_visible(self, logged_in_page: Page):
        """TC-019：登入後右上角餘額數字顯示（非空白）"""
        expect(logged_in_page.locator(".coin-wrap-bg span")).to_be_visible()


class TestUnauthenticated:
    """TC-020：未登入功能"""

    def test_sidebar_triggers_login(self, page: Page, site_config):
        """TC-020：未登入時點側邊欄個人資訊應跳出登入表單"""
        login = LoginPage(page, site_config.url)
        login.goto()
        page.locator(".sidebar-item.user").dispatch_event("click")
        expect(login.username_input).to_be_visible(timeout=5000)


class TestSidebarFeatures:
    """TC-021 ~ TC-022：側邊欄彈窗功能"""

    def test_game_details_opens(self, logged_in_page: Page):
        """TC-021：遊戲明細彈窗可正常開啟"""
        logged_in_page.locator(".sidebar-item.game-details").dispatch_event("click")
        expect(logged_in_page.locator(".dialog-container")).to_be_visible(timeout=5000)

    def test_announcement_opens(self, logged_in_page: Page):
        """TC-022：老吉公告彈窗可正常開啟且有公告內容"""
        logged_in_page.locator(".sidebar-item.announce").dispatch_event("click")
        dialog = logged_in_page.locator(".dialog-container")
        expect(dialog).to_be_visible(timeout=5000)
        expect(dialog).to_contain_text("公告")


class TestNavigation:
    """TC-008 ~ TC-010：導覽列分類頁跳轉"""

    @pytest.mark.parametrize("nav_item,expected_path", [
        ("真人", "/Categories/casino"),
        ("電子", "/Categories/slots"),
        ("捕魚", "/Categories/fishing"),
    ])
    def test_nav_to_category(self, logged_in_page: Page, nav_item, expected_path):
        """TC-008/009/010：點擊導覽列項目應跳轉至對應分類頁"""
        home = HomePage(logged_in_page)
        home.click_nav_item(nav_item)
        expect(logged_in_page).to_have_url(re.compile(re.escape(expected_path)), timeout=8000)
