"""
drc 站點測試專用 conftest
覆寫 site_config fixture，讓 tests/drc/ 下的測試不需加 --site=drc 即可執行
"""

import pytest
from config.settings import get_site_config


@pytest.fixture(scope="session")
def site_config():
    """固定使用 drc 站設定"""
    return get_site_config("drc")
