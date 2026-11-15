import os
import tempfile
from pathlib import Path

import gradio as gr
import pandas as pd
import requests
import urllib3
from fastapi import FastAPI
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_DIR = Path(__file__).parent
PWA_DIR = BASE_DIR / "pwa"

DEFAULT_URL = "https://data.tainan.gov.tw/File/ResourceCsvDownload/6c16b2c8-92b6-49d9-98b5-02966462172c"  # 換連結
TMP_DIR = tempfile.gettempdir()
CSV_PATH = os.path.join(TMP_DIR, "data01.csv")


def placeholder(msg):
    return pd.DataFrame({"提示": [msg]})


# ---------------- 核心邏輯 ----------------
def load_data(url, drop_na):
    try:
        response = requests.get(url.strip(), verify=False, timeout=30)
        response.raise_for_status()
        with open(CSV_PATH, "wb") as f:
            f.write(response.content)

        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")  # 繁體中文
        raw_rows = len(df)
        if drop_na:
            df = df.dropna()

        if len(df) == 0:
            info = (
                "### ⚠️ 載入成功,但沒有資料\n"
                f"原始筆數 {raw_rows},移除缺失值後為 0 筆,請取消勾選 dropna 再試。"
            )
            return placeholder("沒有可顯示的資料"), info, gr.update(choices=[], value=None), pd.DataFrame()

        info = (
            "### ✅ 載入成功\n"
            f"- 原始筆數:**{raw_rows}**\n"
            f"- 目前筆數:**{len(df)}**\n"
            f"- 欄位數:**{len(df.columns)}**"
        )
        return df, info, gr.update(choices=list(df.columns), value=None), df
    except Exception as e:
        return (
            placeholder("載入失敗"),
            f"### ❌ 載入失敗\n`{e}`",
            gr.update(choices=[], value=None),
            pd.DataFrame(),
        )


def search_data(df, column, keyword):
    if df is None or len(df) == 0:
        return placeholder("請先載入資料")
    if not keyword:
        return df
    if column:
        mask = df[column].astype(str).str.contains(keyword, case=False, na=False)
    else:
        mask = (
            df.astype(str)
            .apply(lambda col: col.str.contains(keyword, case=False, na=False))
            .any(axis=1)
        )
    result = df[mask]
    return result if len(result) else placeholder("查無符合的資料")


def export_csv(df):
    if df is None or len(df) == 0 or list(df.columns) == ["提示"]:
        return gr.update(value=None, visible=False)
    out = os.path.join(TMP_DIR, "export.csv")
    df.to_csv(out, index=False, encoding="utf-8-sig")
    return gr.update(value=out, visible=True)


def describe(df):
    if df is None or len(df) == 0:
        return placeholder("請先載入資料")
    return df.describe(include="all").T.reset_index().rename(columns={"index": "欄位"})


# ---------------- PWA:<head> 注入 ----------------
HEAD = """
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0d9488">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="臺南開放資料">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/icons/icon-192.png">
<script>
  // 註冊 Service Worker(需 HTTPS 或 localhost)
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", function () {
      navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function (e) {
        console.warn("SW 註冊失敗:", e);
      });
    });
  }

  // 自訂「安裝成 App」按鈕(Chrome / Edge / Android)
  var deferredPrompt = null;
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (document.getElementById("pwa-install")) return;
    var b = document.createElement("button");
    b.id = "pwa-install";
    b.textContent = "📲 安裝成 App";
    b.onclick = async function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      b.remove();
    };
    document.body.appendChild(b);
  });
  window.addEventListener("appinstalled", function () {
    var b = document.getElementById("pwa-install");
    if (b) b.remove();
  });
</script>
"""

# ---------------- 介面(RWD) ----------------
theme = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Noto Sans TC"), "sans-serif"],
)

css = """
/* 外層容器:寬螢幕置中、手機貼齊並避開瀏海 */
.gradio-container {
  max-width: 1200px !important;
  margin: 0 auto !important;
  padding-left: max(12px, env(safe-area-inset-left)) !important;
  padding-right: max(12px, env(safe-area-inset-right)) !important;
  padding-bottom: max(12px, env(safe-area-inset-bottom)) !important;
}

/* 標題:字級隨螢幕縮放 */
.header {
  text-align: center;
  padding: clamp(12px, 3vw, 20px);
  border-radius: 16px;
  background: linear-gradient(135deg, #0d9488, #0891b2);
}
.header h1 { margin: 0; font-size: clamp(1.3rem, 4.5vw, 2rem); color: #ffffff !important; }
.header p  { margin: 4px 0 0; font-size: clamp(.8rem, 2.6vw, 1rem); color: #ffffff !important; opacity: .92; }

/* 觸控友善:按鈕至少 44px 高 */
button, .gr-button { min-height: 44px; }

/* 平板與手機:橫列改為直向堆疊 */
@media (max-width: 768px) {
  .stack-mobile { flex-direction: column !important; align-items: stretch !important; }
  .stack-mobile > * { width: 100% !important; min-width: 100% !important; flex: 1 1 100% !important; }
  .gradio-container { padding-top: max(8px, env(safe-area-inset-top)) !important; }
}

/* 已安裝為 App(獨立視窗)時:隱藏頁尾並避開狀態列 */
@media (display-mode: standalone) {
  footer { display: none !important; }
  .gradio-container { padding-top: max(8px, env(safe-area-inset-top)) !important; }
}

/* 安裝按鈕 */
#pwa-install {
  position: fixed; right: max(16px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom)); z-index: 9999;
  min-height: 48px; padding: 0 20px; border: 0; border-radius: 999px;
  font-size: 1rem; font-weight: 700; color: #fff; cursor: pointer;
  background: linear-gradient(135deg, #0d9488, #0891b2);
  box-shadow: 0 6px 18px rgba(13, 148, 136, .45);
}
"""

with gr.Blocks(theme=theme, css=css, head=HEAD, title="臺南市開放資料檢視器") as demo:
    gr.HTML(
        """
        <div class="header">
          <h1>📊 臺南市開放資料檢視器</h1>
          <p>下載、清理、搜尋並匯出政府開放資料 CSV</p>
        </div>
        """
    )

    full_df = gr.State(pd.DataFrame())

    with gr.Row(equal_height=True, elem_classes="stack-mobile"):
        url_box = gr.Textbox(label="🔗 CSV 連結", value=DEFAULT_URL, lines=1, scale=4)
        with gr.Column(scale=1, min_width=200):
            drop_na = gr.Checkbox(label="移除缺失值 (dropna)", value=True)
            load_btn = gr.Button("🚀 載入資料", variant="primary")

    info_md = gr.Markdown("請按下「載入資料」開始。")

    with gr.Tabs():
        with gr.Tab("📋 資料表"):
            with gr.Row(equal_height=True, elem_classes="stack-mobile"):
                col_dd = gr.Dropdown(label="搜尋欄位(留空=全部欄位)", choices=[], value=None, scale=2)
                kw_box = gr.Textbox(label="關鍵字", placeholder="輸入想搜尋的文字…", scale=3)
                search_btn = gr.Button("🔍 搜尋", variant="secondary", scale=1, min_width=120)

            table = gr.Dataframe(
                value=placeholder("請先按「載入資料」"),
                label="資料內容",
                interactive=False,
                wrap=True,
                max_height=480,
            )

            export_btn = gr.Button("💾 匯出目前結果為 CSV")
            file_out = gr.File(label="下載檔案", visible=False, height=110)

        with gr.Tab("📈 統計摘要"):
            stat_btn = gr.Button("產生統計摘要")
            stat_table = gr.Dataframe(
                value=placeholder("按下上方按鈕產生統計摘要"),
                label="describe()",
                interactive=False,
                max_height=480,
            )

    # ---------------- 事件 ----------------
    load_btn.click(load_data, [url_box, drop_na], [table, info_md, col_dd, full_df])
    search_btn.click(search_data, [full_df, col_dd, kw_box], table)
    kw_box.submit(search_data, [full_df, col_dd, kw_box], table)
    export_btn.click(export_csv, table, file_out)
    stat_btn.click(describe, full_df, stat_table)


# ---------------- FastAPI:PWA 路由 + 掛載 Gradio ----------------
app = FastAPI()


@app.get("/manifest.webmanifest")
def manifest():
    return FileResponse(PWA_DIR / "manifest.webmanifest", media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    # 必須由根路徑提供,Service Worker 才能控制整個網站
    return FileResponse(
        PWA_DIR / "sw.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


@app.get("/offline")
def offline():
    return FileResponse(PWA_DIR / "offline.html", media_type="text/html")


@app.get("/healthz")
def healthz():
    return PlainTextResponse("ok")


app.mount("/icons", StaticFiles(directory=PWA_DIR / "icons"), name="icons")

# 必須放在所有自訂路由之後(掛載在 "/" 會接手其餘請求)
app = gr.mount_gradio_app(app, demo, path="/")


if __name__ == "__main__":
    import uvicorn

    # Render 會提供 PORT 環境變數,且必須綁定 0.0.0.0
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 7860)))
