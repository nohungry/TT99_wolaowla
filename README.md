# Auto Regression - Platform 自動化回歸測試

使用 **Python + pytest-playwright**，針對 T9 Platform 遊戲站台進行端對端回歸測試，支援 Windows、WSL、Linux 三種環境自動偵測。

## 支援站台

| 站台 ID | 網址 | 測試數 |
|---------|------|--------|
| `drc` | dev-drc.t9platform-ph.com | 27 |
| `dlt` | dev-lt.t9platform.com | 72 |

## 目錄結構

```
conftest.py                    — 全域 fixtures、環境偵測、MutationObserver 注入
config/settings.py             — 多站台 SiteConfig，從 .env 讀取
pages/factory.py               — site_id → LoginPage/HomePage 路由
pages/drc/                     — drc 站 Page Objects
pages/dlt/                     — dlt 站 Page Objects
tests/drc/                     — drc 站測試（test_p0_smoke.py、test_functional.py）
tests/dlt/                     — dlt 站測試（test_p0_smoke.py、test_functional.py、test_locale_visual_matrix.py）
tests/dlt/__snapshots__/       — Visual Regression baseline 截圖
utils/locale_helper.py         — set_locale()：注入 i18n_redirected_lt cookie
utils/dialog_helper.py         — 伺服器錯誤彈窗關閉、Loading 等待
utils/screenshot_helper.py     — 截圖系統（元素高亮 + 自動產生繁中 README）
screenshots/vr_reference/      — home_shell / member_menu 截圖存檔（不比對，供人工確認）
reports/report.html            — pytest-html 測試報表
```

## 安裝

```bash
cp .env.example .env        # 填入站台帳號密碼與 CDP_URL
pip install -r requirements.txt
playwright install chromium
```

## 執行

**請使用專案 virtualenv（`.venv/`）執行所有指令。**

```bash
.venv/bin/pytest                                                          # 全部測試
.venv/bin/pytest tests/drc/                                               # drc 站
.venv/bin/pytest tests/dlt/                                               # dlt 站
.venv/bin/pytest tests/dlt/test_p0_smoke.py -m p0                        # dlt P0 smoke
.venv/bin/pytest -m p0                                                    # 所有站台 P0
.venv/bin/pytest tests/drc/test_p0_smoke.py::TestLogin::test_login_success # 單一測試
```

### Visual Regression（WIN-VR / WIN-LVIS）

```bash
# 首次建立 baseline（或環境變更後更新）
.venv/bin/pytest tests/dlt/test_functional.py -m visual_regression --update-snapshots
.venv/bin/pytest tests/dlt/test_locale_visual_matrix.py --update-snapshots

# 後續比對
.venv/bin/pytest tests/dlt/test_functional.py -m visual_regression
.venv/bin/pytest tests/dlt/test_locale_visual_matrix.py
```

> **注意：** `test_home_shell` 與 `test_member_menu` 因首頁含動態內容（公告跑馬燈、熱門遊戲排序），截圖僅存檔至 `screenshots/vr_reference/`，不做 baseline 比對。

### 查看 HTML 報表

```bash
explorer.exe reports/report.html   # WSL
```

## WSL 設定

### 1. 設定 Port Proxy（Windows PowerShell，系統管理員）

```powershell
netsh interface portproxy add v4tov4 listenaddress=<WINDOWS_IP> listenport=9223 connectaddress=127.0.0.1 connectport=9223
```

### 2. 設定 .env

```
CDP_URL=http://<WINDOWS_IP>:9223
```

查詢 Windows IP：
```bash
cat /etc/resolv.conf | grep nameserver
```

### 3. 執行測試

`conftest.py` 偵測到 WSL 後，若 Chrome 尚未啟動會自動呼叫 `chrome.exe --remote-debugging-port=9223`，不需手動開啟瀏覽器。

## 環境對照

| 環境 | 瀏覽器啟動方式 |
|------|----------------|
| Windows | Playwright 直接啟動 |
| WSL | 自動啟動 Windows Chrome，透過 CDP 連接（port 9223） |
| Linux | 手動啟動 Chrome `--remote-debugging-port=9222`，設定 `CDP_URL` |

Port 轉發與環境設定細節請參考 [PORTS_AND_SETUP.md](PORTS_AND_SETUP.md)。

## 測試分級

| Marker | 說明 |
|--------|------|
| `p0` | 核心 Smoke，每次 Release 必跑 |
| `p1` | 功能驗證，重大版本必跑 |
| `p2` | 視覺回歸，完整回歸才跑 |
| `login` | 登入相關 |
| `home` | 首頁相關 |
| `visual_regression` | WIN-VR 截圖比對 |
| `locale_visual` | WIN-LVIS 多語系截圖矩陣 |

## 說明

- 多站台支援：在 `.env` 增加 `SITE_XXX_URL / SITE_XXX_USERNAME / SITE_XXX_PASSWORD`，放在 `tests/xxx/` 下即可
- `conftest.py` 內建 MutationObserver 注入，自動處理「伺服器錯誤」彈窗（drc 站）
- 報表輸出至 `reports/report.html`，已加入 `.gitignore`
- 每個測試自動截圖並高亮操作元素（紅框），存於 `screenshots/<test_name>/`，並產生繁中操作流程 README；`screenshots/` 已加入 `.gitignore`
