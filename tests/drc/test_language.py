"""
多語系檢查測試
- TC-L01：語系下拉選單應有 6 個語系
- TC-L02：切換各語系後，登入表單欄位 placeholder 正確對應該語系

不需要登入，使用 page fixture（function-scoped）。
兩個驗證點合併為單一測試，只開一次瀏覽器。

執行方式：
    .venv/bin/pytest tests/drc/test_language.py -v
    .venv/bin/pytest -m language -v
"""

import pytest
from playwright.sync_api import Page, expect, TimeoutError as PlaywrightTimeoutError
from utils.dialog_helper import dismiss_server_error_if_present
from utils.screenshot_helper import get_screenshotter


# 各語系名稱與登入表單 placeholder 預期值
# name 必須與頁面下拉選單的文字完全一致
LANGUAGES = [
    {"name": "繁體中文", "username_ph": "用戶名",      "password_ph": "密碼"},
    {"name": "簡体中文", "username_ph": "用户名",      "password_ph": "密码"},
    {"name": "日本語",   "username_ph": "ユーザー名",  "password_ph": "パスワード"},
    {"name": "ภาษาไทย", "username_ph": "ชื่อผู้ใช้",  "password_ph": "รหัสผ่าน"},
    {"name": "Tiếng Việt", "username_ph": "Tên người dùng", "password_ph": "Mật khẩu"},
    {"name": "English",  "username_ph": "Username",    "password_ph": "Password"},
]

EXPECTED_LANG_COUNT = 6


def _get_lang_dropdown(page: Page):
    """取得語系下拉選單容器（globe icon 的父層 relative div 內的選單）"""
    return page.locator("img[src*='global']").locator("..").locator("p.whitespace-nowrap")


def _open_lang_dropdown(page: Page):
    """點擊語系切換 icon（🌐）開啟下拉選單"""
    globe = page.locator("img[src*='global']")
    globe.scroll_into_view_if_needed()
    globe.click()
    # 等待下拉選單出現
    _get_lang_dropdown(page).first.wait_for(state="visible", timeout=5000)


@pytest.mark.p1
@pytest.mark.language
class TestLanguage:
    """TC-L01 / TC-L02：多語系切換與登入表單驗證"""

    def test_language_dropdown_and_login_placeholders(self, page: Page, site_config):
        """TC-L01/L02：語系選單應有 6 個語系，各語系登入表單 placeholder 正確"""
        page.goto(site_config.url)
        page.wait_for_load_state("networkidle")
        dismiss_server_error_if_present(page)
        sh = get_screenshotter(page)

        # ===== TC-L01：驗證語系選單有 6 個語系 =====
        _open_lang_dropdown(page)

        # 語系項目：globe icon 父層內的 p.whitespace-nowrap 元素
        lang_items = _get_lang_dropdown(page)
        expect(lang_items).to_have_count(EXPECTED_LANG_COUNT)

        # 逐一驗證語系名稱可見
        for lang in LANGUAGES:
            lang_el = lang_items.filter(has_text=lang["name"])
            expect(lang_el).to_be_visible()

        if sh:
            sh.full_page("verify_語系選單_6個語系")

        # 重載頁面，確保乾淨狀態
        page.goto(site_config.url)
        page.wait_for_load_state("networkidle")
        dismiss_server_error_if_present(page)

        # ===== TC-L02：逐一切換語系，驗證登入表單 placeholder =====
        for lang in LANGUAGES:
            # 開啟語系選單並選擇語系
            _open_lang_dropdown(page)
            lang_option = _get_lang_dropdown(page).filter(has_text=lang["name"])
            if sh:
                sh.capture(lang_option, f"click_選擇語系_{lang['name']}")
            lang_option.click()
            page.wait_for_load_state("networkidle")
            dismiss_server_error_if_present(page)

            # 點擊登入按鈕開啟登入表單（button.primary-btn 各語系共用）
            login_trigger = page.locator("button.primary-btn")
            login_trigger.scroll_into_view_if_needed()
            if sh:
                sh.capture(login_trigger, f"click_登入按鈕_{lang['name']}")
            login_trigger.click()

            # 等待登入表單出現
            username_input = page.locator("input.input-style[type='text']")
            username_input.wait_for(state="visible", timeout=5000)
            password_input = page.locator("input.input-style[type='password']")

            # 驗證 placeholder 文字
            expect(username_input).to_have_attribute(
                "placeholder", lang["username_ph"], timeout=3000
            )
            expect(password_input).to_have_attribute(
                "placeholder", lang["password_ph"], timeout=3000
            )

            # 截圖：框出帳號與密碼欄位
            if sh:
                sh.capture(username_input, f"verify_{lang['name']}_帳號placeholder")
                sh.capture(password_input, f"verify_{lang['name']}_密碼placeholder")
                sh.full_page(f"verify_{lang['name']}_登入表單全頁")

            # 關閉登入彈窗：重新導向回首頁
            page.goto(site_config.url)
            page.wait_for_load_state("networkidle")
            dismiss_server_error_if_present(page)
