#!/usr/bin/env python3
"""生成微信公众号封面图（900x383，微信推荐 2.35:1）。

用法:
    python3 make_cover.py --main "AI 前线" --sub "第 47 期" --foot "11.16 — 11.18" \
        --out assets/thumb.png

可选:
    --theme blue|dark|warm   配色（默认 blue）
    --check                  生成后打印文字包围盒，便于确认无遮挡
"""
import argparse
import os
import sys

from PIL import Image, ImageDraw, ImageFont

W, H = 900, 383

THEMES = {
    "blue": {"top": (8, 140, 255), "bottom": (34, 82, 169), "accent": (255, 205, 60),
             "deco": (20, 110, 220), "sub": (210, 232, 255), "foot": (180, 214, 255)},
    "dark": {"top": (24, 26, 32), "bottom": (8, 9, 12), "accent": (10, 132, 255),
             "deco": (40, 44, 56), "sub": (190, 195, 205), "foot": (140, 146, 158)},
    "warm": {"top": (255, 138, 92), "bottom": (196, 62, 46), "accent": (255, 226, 150),
             "deco": (220, 90, 60), "sub": (255, 232, 218), "foot": (255, 214, 196)},
}

FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]


def pick_font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def build(main, sub, foot, theme, out):
    th = THEMES.get(theme, THEMES["blue"])

    img = Image.new("RGB", (W, H), th["top"])
    d = ImageDraw.Draw(img)
    for y in range(H):
        d.line([(0, y), (W, y)], fill=lerp(th["top"], th["bottom"], y / H))

    # 右下角装饰圆
    overlay = Image.new("RGB", (W, H))
    od = ImageDraw.Draw(overlay)
    od.ellipse([(W - 330, H - 230), (W + 90, H + 190)], fill=th["deco"])
    img = Image.blend(img, overlay, 0.35)
    d = ImageDraw.Draw(img)

    fp = pick_font()
    def f(size):
        return ImageFont.truetype(fp, size) if fp else ImageFont.load_default()

    f_big, f_mid, f_small = f(58), f(30), f(24)

    # 左侧竖条（与文字错开，避免遮挡）
    d.rectangle([(58, 78), (68, 78 + 70)], fill=th["accent"])
    x = 92
    d.text((x, 70), main, font=f_big, fill=(255, 255, 255))
    d.text((x + 2, 160), sub, font=f_mid, fill=th["sub"])
    d.text((x + 2, 212), foot, font=f_small, fill=th["foot"])

    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    img.save(out, "PNG", optimize=True)
    print(f"✓ 封面已生成: {out}  ({os.path.getsize(out)} bytes, {W}x{H})")

    return img, d, f_big, f_mid, f_small, th


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--main", required=True, help="主标题，如 AI 前线")
    ap.add_argument("--sub", default="", help="副标题，如 第 47 期")
    ap.add_argument("--foot", default="", help="底部信息，如日期区间")
    ap.add_argument("--theme", default="blue", choices=list(THEMES))
    ap.add_argument("--out", default="assets/thumb.png")
    ap.add_argument("--check", action="store_true", help="打印文字包围盒")
    a = ap.parse_args()

    img, d, f_big, f_mid, f_small, th = build(a.main, a.sub, a.foot, a.theme, a.out)

    if a.check:
        boxes = [("main", d.textbbox((92, 70), a.main, font=f_big)),
                 ("sub", d.textbbox((94, 160), a.sub, font=f_mid)),
                 ("foot", d.textbbox((94, 212), a.foot, font=f_small))]
        for name, b in boxes:
            ok = b[2] <= W - 20 and b[3] <= H - 10
            print(f"  {name}: bbox={b} {'OK' if ok else '⚠ 超出画布'}")
        print("  ⚠ 请用 Read 工具实际看一眼图片，确认无遮挡/裁切")


if __name__ == "__main__":
    sys.exit(main())
