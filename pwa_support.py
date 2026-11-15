"""PWA 支援:在伺服器端把 PWA 標籤直接寫進 Gradio 首頁的 <head>。

為什麼不用 gr.Blocks(head=...)?
Gradio 前端是頁面載入「之後」才動態插入 head 內容,此時 window 的 load 事件早已觸發,
Service Worker 沒被註冊,Chrome 就不會顯示安裝圖示。
改成伺服器端直接改寫 HTML,標籤與腳本在頁面一開始就存在,最穩定。
"""
import re

PWA_HEAD = """
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#0d9488">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="臺南開放資料">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="apple-touch-icon" href="/icons/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/icons/icon-192.png">
<script>
(function () {
  // 註冊 Service Worker(需 HTTPS 或 localhost)
  function registerSW() {
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(function (e) {
      console.warn("SW 註冊失敗:", e);
    });
  }
  if ("serviceWorker" in navigator) {
    if (document.readyState === "complete") registerSW();
    else window.addEventListener("load", registerSW);
  }

  // 自訂「安裝成 App」按鈕(Chrome / Edge / Android)
  var deferredPrompt = null;
  function showButton() {
    if (document.getElementById("pwa-install")) return;
    var b = document.createElement("button");
    b.id = "pwa-install";
    b.type = "button";
    b.textContent = "📲 安裝成 App";
    b.onclick = async function () {
      if (!deferredPrompt) return;
      deferredPrompt.prompt();
      await deferredPrompt.userChoice;
      deferredPrompt = null;
      b.remove();
    };
    (document.body || document.documentElement).appendChild(b);
  }
  window.addEventListener("beforeinstallprompt", function (e) {
    e.preventDefault();
    deferredPrompt = e;
    if (document.body) showButton();
    else document.addEventListener("DOMContentLoaded", showButton);
  });
  window.addEventListener("appinstalled", function () {
    var b = document.getElementById("pwa-install");
    if (b) b.remove();
  });
})();
</script>
"""


def inject_pwa(html: str) -> str:
    """把 lang 改成 zh-TW(避免瀏覽器誤跳翻譯),並在 </head> 前插入 PWA 標籤。"""
    if "/manifest.webmanifest" in html:  # 已注入過
        return html

    if re.search(r"<html[^>]*\blang=", html, re.I):
        html = re.sub(
            r"""(<html[^>]*?\blang=)(["']).*?\2""",
            lambda m: m.group(1) + '"zh-TW"',
            html,
            count=1,
            flags=re.I,
        )
    else:
        html = re.sub(r"<html", '<html lang="zh-TW"', html, count=1, flags=re.I)

    return re.sub(r"</head>", lambda m: PWA_HEAD + "</head>", html, count=1, flags=re.I)


class PWAInjectMiddleware:
    """純 ASGI 中介層:只改寫首頁 "/" 的 HTML,其餘請求原封不動。"""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["method"] != "GET" or scope["path"] != "/":
            return await self.app(scope, receive, send)

        # 要求內層不要壓縮,才能改寫 HTML
        scope = dict(scope)
        scope["headers"] = [(k, v) for k, v in scope["headers"] if k.lower() != b"accept-encoding"]

        state = {"start": None, "chunks": []}

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                state["start"] = message
                return
            if message["type"] != "http.response.body":
                return await send(message)

            state["chunks"].append(message.get("body", b""))
            if message.get("more_body"):
                return

            start, body = state["start"], b"".join(state["chunks"])
            headers = list(start["headers"])
            names = {k.lower(): v for k, v in headers}
            is_html = start["status"] == 200 and b"text/html" in names.get(b"content-type", b"")
            if is_html and b"content-encoding" not in names:
                body = inject_pwa(body.decode("utf-8")).encode("utf-8")
                headers = [(k, v) for k, v in headers if k.lower() != b"content-length"]
                headers.append((b"content-length", str(len(body)).encode()))
                start = {**start, "headers": headers}
            await send(start)
            await send({"type": "http.response.body", "body": body})

        await self.app(scope, receive, wrapped_send)
