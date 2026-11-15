import os
import tempfile

import gradio as gr
import pandas as pd
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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


# ---------------- 介面 ----------------
theme = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="cyan",
    neutral_hue="slate",
    font=[gr.themes.GoogleFont("Noto Sans TC"), "sans-serif"],
)

css = """
.header {text-align:center; padding:18px; border-radius:16px;
         background:linear-gradient(135deg,#0d9488,#0891b2);}
.header h1 {margin:0; font-size:2rem; color:#ffffff !important;}
.header p  {margin:4px 0 0; color:#ffffff !important; opacity:.92;}
"""

with gr.Blocks(theme=theme, css=css, title="臺南市開放資料檢視器") as demo:
    gr.HTML(
        """
        <div class="header">
          <h1>📊 臺南市開放資料檢視器</h1>
          <p>下載、清理、搜尋並匯出政府開放資料 CSV</p>
        </div>
        """
    )

    full_df = gr.State(pd.DataFrame())

    with gr.Row(equal_height=True):
        url_box = gr.Textbox(label="🔗 CSV 連結", value=DEFAULT_URL, lines=1, scale=4)
        with gr.Column(scale=1, min_width=200):
            drop_na = gr.Checkbox(label="移除缺失值 (dropna)", value=True)
            load_btn = gr.Button("🚀 載入資料", variant="primary")

    info_md = gr.Markdown("請按下「載入資料」開始。")

    with gr.Tabs():
        with gr.Tab("📋 資料表"):
            with gr.Row(equal_height=True):
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


if __name__ == "__main__":
    # Render 會提供 PORT 環境變數,且必須綁定 0.0.0.0
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
