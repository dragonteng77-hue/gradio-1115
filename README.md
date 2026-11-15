# 📊 臺南市開放資料檢視器

使用 **Gradio** 打造的政府開放資料 CSV 檢視工具:下載、清理、搜尋、統計並匯出。

## ✨ 功能

- 🔗 自訂 CSV 連結(預設為臺南市政府資料開放平台)
- 🧹 可選擇是否移除缺失值(`dropna`)
- 🔍 依欄位或全欄位關鍵字搜尋
- 📈 一鍵產生統計摘要
- 💾 匯出目前結果為 UTF-8-sig CSV(Excel 開啟不亂碼)

## 📁 專案結構

```
.
├── app.py             # 主程式
├── requirements.txt   # 相依套件
├── render.yaml        # Render Blueprint 設定(選用)
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

開啟瀏覽器前往 http://127.0.0.1:7860

## 🚀 部署到 Render

1. 將此專案推送到 GitHub。
2. 登入 [Render](https://render.com),選擇 **New → Web Service**,連結你的 GitHub repo。
3. 設定如下:

| 欄位 | 值 |
|------|----|
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python app.py` |
| Instance Type | Free(或依需求) |

4.(建議)在 **Environment** 新增變數 `PYTHON_VERSION` = `3.11.9`。
5. 按下 **Create Web Service**,等待建置完成即可取得公開網址。

也可以使用專案內的 `render.yaml`:在 Render 選擇 **New → Blueprint**,連結 repo 後會自動套用上述設定。

> `app.py` 會自動讀取 Render 提供的 `PORT` 環境變數,並綁定 `0.0.0.0`,不需額外修改。

### ⚠️ 注意事項

- Render 免費方案閒置一段時間後會休眠,第一次開啟需等待數十秒喚醒。
- 下載的 CSV 存放於暫存目錄,重新部署或重啟後會消失,屬正常現象。
- 因政府網站憑證問題,程式以 `verify=False` 下載資料,僅適用於公開資料。

## 🔄 更換資料來源

修改 `app.py` 中的 `DEFAULT_URL`,或直接在網頁介面的「CSV 連結」欄位貼上新的連結。

## 📜 授權

MIT License
