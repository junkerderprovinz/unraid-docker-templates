#!/usr/bin/env python3
"""Generate the README-only card icons in this folder from each app's CA icon.

These icons are shown ONLY in the root README cards — they are NOT the Community
Applications icons (those stay at ``<app>/icon.png``). Each one gets a white
background and rounded corners (matching Krusader's corner radius). Standard Notes
logos are cropped edge-to-edge. Krusader keeps its own transparent icon and is not
generated here.

GitHub strips CSS, so the white background + rounding must be baked into the PNG.

Usage:  python .github/readme-icons/generate.py      (requires Pillow)
"""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))

# README-card icons to generate (every app except Krusader, which stays transparent)
APPS = ["featherdrop", "jdownloader", "matrix", "openhands",
        "n8n", "standardnotes-server", "standardnotes-webui"]
# logos to crop and centre with a small white margin (Standard Notes)
MARGIN_LOGOS = {"standardnotes-server", "standardnotes-webui"}
LOGO_FILL = 0.82  # fraction of the tile the cropped logo fills (rest = white margin)


def krusader_corner_ratio():
    """Estimate Krusader's corner radius as a fraction of icon width (the reference)."""
    k = Image.open(os.path.join(ROOT, "krusader", "icon.png")).convert("RGBA")
    l, t, r, b = k.split()[3].getbbox()
    bw = r - l
    px = k.load()
    rad = 0
    for x in range(l, r):
        if px[x, t + 1][3] > 128:
            rad = x - l
            break
    ratio = rad / bw if bw else 0.141
    return ratio if 0.05 <= ratio <= 0.45 else 0.141


def add_rounded_corners(im, ratio):
    w, h = im.size
    rr = int(round(ratio * w))
    ss = 4  # supersample for a smooth (anti-aliased) mask
    big = Image.new("L", (w * ss, h * ss), 0)
    ImageDraw.Draw(big).rounded_rectangle([0, 0, w * ss - 1, h * ss - 1], radius=rr * ss, fill=255)
    im.putalpha(big.resize((w, h), Image.LANCZOS))
    return im


def content_bbox(im):
    """Bounding box of non-white, opaque pixels (the logo)."""
    w, h = im.size
    px = im.load()
    minx, miny, maxx, maxy = w, h, 0, 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a > 16 and not (r > 245 and g > 245 and b > 245):
                minx, maxx = min(minx, x), max(maxx, x)
                miny, maxy = min(miny, y), max(maxy, y)
    return (minx, miny, maxx + 1, maxy + 1)


def main():
    ratio = krusader_corner_ratio()
    print(f"corner ratio (from Krusader): {ratio:.3f}")
    for app in APPS:
        src = Image.open(os.path.join(ROOT, app, "icon.png")).convert("RGBA")
        w, h = src.size
        canvas = Image.new("RGBA", (w, h), (255, 255, 255, 255))
        if app in MARGIN_LOGOS:
            logo = src.crop(content_bbox(src))
            target = int(round(min(w, h) * LOGO_FILL))
            lw, lh = logo.size
            s = target / max(lw, lh)
            logo = logo.resize((max(1, round(lw * s)), max(1, round(lh * s))), Image.LANCZOS)
            canvas.paste(logo, ((w - logo.size[0]) // 2, (h - logo.size[1]) // 2))
        else:
            canvas = Image.alpha_composite(canvas, src)
            corner = canvas.load()[0, 0]
            if corner[:3] != (255, 255, 255):  # opaque non-white bg (e.g. featherdrop #121212) -> white
                cr, cg, cb = corner[:3]
                tol = 26
                px = canvas.load()
                for y in range(h):
                    for x in range(w):
                        r, g, b, a = px[x, y]
                        if abs(r - cr) <= tol and abs(g - cg) <= tol and abs(b - cb) <= tol:
                            px[x, y] = (255, 255, 255, 255)
        add_rounded_corners(canvas, ratio).save(os.path.join(HERE, app + ".png"))
        print("wrote", app + ".png")


if __name__ == "__main__":
    main()
