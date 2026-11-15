# 📊 臺南市開放資料檢視器

使用 **Gradio** 打造的政府開放資料 CSV 檢視工具,支援 **PWA(可安裝成 App)** 與 **RWD(手機/平板/桌機自適應)**。

## ✨ 功能

- 🔗 自訂 CSV 連結(預設為臺南市政府資料開放平台)
- 🧹 可選擇是否移除缺失值(`dropna`)
- 🔍 依欄位或全欄位關鍵字搜尋
- 📈 一鍵產生統計摘要
- 💾 匯出目前結果為 UTF-8-sig CSV(Excel 開啟不亂碼)
- 📲 PWA:可加入主畫面、獨立視窗執行、離線時顯示提示頁
- 📱 RWD:手機自動直向堆疊、觸控按鈕 ≥ 44px、支援瀏海安全區

## 📁 專案結構

```
.
├── app.py                    # 主程式(FastAPI + Gradio)
├── pwa_support.py           # PWA 標籤伺服器端注入(中介層)
├── requirements.txt          # 相依套件
├── render.yaml               # Render Blueprint 設定(選用)
├── make_icons.py             # 圖示產生器(選用,需 pillow)
├── pwa/
│   ├── manifest.webmanifest  # Web App Manifest
│   ├── sw.js                 # Service Worker
│   ├── offline.html          # 離線提示頁
│   └── icons/                # 192 / 512 / maskable / apple-touch
├── .gitignore
└── README.md
```

## 💻 本機執行

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

開啟瀏覽器前往 http://127.0.0.1:7860 (`localhost` 可直接測試 PWA,不需 HTTPS)。

## 🚀 部署到 Render

1. 將此專案推送到 GitHub。
2. 登入 [Render](https://render.com),選擇 **New → Web Service**,連結 repo。
3. 設定如下:

| 欄位 | 值 |
|------|----|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python app.py` |
| Health Check Path | `/healthz`(選用) |

4.(建議)在 **Environment** 新增 `PYTHON_VERSION` = `3.11.9`。
5. 按下 **Create Web Service**。

也可使用 `render.yaml`:選擇 **New → Blueprint** 連結 repo 即可自動套用。

> Render 預設提供 HTTPS,正是 PWA 安裝所需條件。`app.py` 會自動讀取 `PORT` 環境變數並綁定 `0.0.0.0`。

## 📲 安裝成 App

| 平台 | 方式 |
|------|------|
| Android Chrome | 點頁面右下角「📲 安裝成 App」,或選單 → 安裝應用程式 |
| 桌面 Chrome / Edge | 網址列右側的安裝圖示 |
| iPhone / iPad Safari | 分享 → 加入主畫面(iOS 不會出現安裝按鈕) |

## 🔧 PWA 運作說明

- `/manifest.webmanifest`、`/sw.js`、`/offline`、`/icons/*` 由 FastAPI 在**根路徑**提供,Service Worker 才能控制整個網站。
- **PWA 標籤由伺服器端注入**:`pwa_support.py` 的中介層會改寫首頁 HTML,在 `<head>` 加入 manifest、圖示、Service Worker 註冊腳本,並把 `lang` 改成 `zh-TW`(避免 Chrome 誤跳出翻譯)。
  - 不使用 `gr.Blocks(head=...)`:Gradio 前端是頁面載入後才動態插入 head,此時 `load` 事件已過,Service Worker 不會被註冊。
- Service Worker 策略:
  - 頁面導覽:網路優先,斷線時顯示 `/offline`
  - `/assets`、`/static`、`/icons`:快取優先
  - Gradio 的 API、佇列、上傳:一律走網路,不快取
- 此工具需要連線才能下載資料,因此「離線」僅提供提示頁,不是完整離線功能。
- **改版後**請修改 `pwa/sw.js` 的 `VERSION`(例如 `v2`),讓使用者端更新快取。
- 圖示可修改 `make_icons.py` 的顏色與圖形後重新執行:`pip install pillow && python make_icons.py`。

## 🩺 PWA 檢查清單

部署後如果網址列沒有安裝圖示,依序確認:

1. 直接開 `https://你的網址/manifest.webmanifest`,應該看到 JSON(看到 Gradio 畫面代表部署的不是這個版本)。
2. 開 `https://你的網址/sw.js`,應該看到 JavaScript 程式碼。
3. Chrome 開發者工具 → **Application** → **Manifest** 看有沒有錯誤,**Service Workers** 看狀態是否為 activated。
4. 若曾裝過舊版,先在 Service Workers 按 **Unregister**、Storage 按 **Clear site data**,再強制重新整理(Ctrl+Shift+R)。
5. 已安裝過的網站,Chrome 不會再顯示安裝圖示。

## ⚠️ 注意事項

- Render 免費方案閒置後會休眠,第一次開啟需等待數十秒喚醒。
- 下載的 CSV 存放於暫存目錄,重新部署或重啟後會消失,屬正常現象。
- 因政府網站憑證問題,程式以 `verify=False` 下載資料,僅適用於公開資料。
- Google Colab 無法使用 PWA(沒有可安裝的固定網域與根路徑),請在 Render 或本機執行。

## 🔄 更換資料來源

修改 `app.py` 中的 `DEFAULT_URL`,或直接在網頁的「CSV 連結」欄位貼上新的連結。

## 📜 授權

MIT License
