"""
Page Object Factory
根據 site_id 回傳對應站點的 Page Object class
"""


def get_login_page_class(site_id: str):
    """根據 site_id 回傳對應的 LoginPage class"""
    if site_id == 'dlt':
        from pages.dlt.login_page import LoginPage
    else:
        from pages.drc.login_page import LoginPage
    return LoginPage


def get_home_page_class(site_id: str):
    """根據 site_id 回傳對應的 HomePage class"""
    if site_id == 'dlt':
        from pages.dlt.home_page import HomePage
    else:
        from pages.drc.home_page import HomePage
    return HomePage
