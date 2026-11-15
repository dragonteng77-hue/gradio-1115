"""產生 PWA 圖示(需要 Pillow:pip install pillow)。圖示已預先產生並放在 pwa/icons/,一般不需重跑。"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).parent / "pwa" / "icons"
OUT.mkdir(parents=True, exist_ok=True)
C1, C2 = (13, 148, 136), (8, 145, 178)  # teal -> cyan


def gradient(size):
    img = Image.new("RGB", (size, size))
    px = []
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * (size - 1))
            px.append(tuple(int(C1[i] + (C2[i] - C1[i]) * t) for i in range(3)))
    img.putdata(px)
    return img


def glyph(img):
    s = img.size[0]
    d = ImageDraw.Draw(img)
    box = s * 0.5
    x0 = y0 = (s - box) / 2
    bw, gap = box * 0.2, box * 0.1
    sx = x0 + (box - (3 * bw + 2 * gap)) / 2
    base = y0 + box
    for i, h in enumerate((0.45, 0.75, 1.0)):
        left = sx + i * (bw + gap)
        d.rounded_rectangle([left, base - box * h, left + bw, base], radius=bw * 0.25, fill="white")
    return img


def full_bleed(size):
    return glyph(gradient(size))


def rounded(size):
    img = full_bleed(size).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    img.putalpha(mask)
    return img


rounded(192).save(OUT / "icon-192.png")
rounded(512).save(OUT / "icon-512.png")
full_bleed(512).save(OUT / "icon-maskable-512.png")   # maskable:滿版,內容在安全區內
full_bleed(180).save(OUT / "apple-touch-icon.png")    # iOS 不支援透明
print("icons done")
