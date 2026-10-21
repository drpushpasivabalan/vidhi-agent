"""Render synthetic official-looking documents for VIDHI-Bench.

Every image carries a 'SYNTHETIC RESEARCH SAMPLE - NOT AN OFFICIAL DOCUMENT' band,
uses no emblems or logos, and only invented names and numbers.
Document features that procedure checks rely on (DIN line, QR code + passcode,
court-seal image, 'digitally signed' line, cited sections) are rendered as real
pixels, so the system must recover them with OCR / QR decoding / seal detection.
"""
from __future__ import annotations

import io
import random
import sys

import numpy as np
import qrcode
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from vidhi.paths import MMFLAG_PATH, add  # noqa: E402
add(MMFLAG_PATH)
from samples.make_images import jpeg, scan  # noqa: E402

F = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
W, H = 1000, 1300


def font(sz, b=False):
    return ImageFont.truetype(FB if b else F, sz)


def _wrap(d, text, x, y, fnt, maxw, fill=25, lh=34):
    words, line = text.split(), ""
    for w in words:
        t = (line + " " + w).strip()
        if d.textlength(t, font=fnt) > maxw:
            d.text((x, y), line, font=fnt, fill=fill)
            y += lh
            line = w
        else:
            line = t
    if line:
        d.text((x, y), line, font=fnt, fill=fill)
        y += lh
    return y


def _seal(d, cx, cy, r, label, rng):
    for k, rr in enumerate(range(r, 26, -8)):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=60 + (k % 3) * 25, width=3)
    for a in np.linspace(0, 2 * np.pi, 32, endpoint=False):
        d.line((cx + 30 * np.cos(a), cy + 30 * np.sin(a), cx + 52 * np.cos(a), cy + 52 * np.sin(a)), fill=70, width=2)
    d.text((cx, cy), label, font=font(22, True), anchor="mm", fill=40)


def render(spec: dict, rng: random.Random) -> tuple[Image.Image, dict]:
    """spec keys: header, title, ref, date, to, body (list[str]), din, qr_url, passcode,
    seal (bool), ds_name, signatory, manip (None|'copy_move'|'splice')."""
    img = Image.new("L", (W, H), 250)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W, 34), fill=200)
    d.text((W // 2, 17), "SYNTHETIC RESEARCH SAMPLE - NOT AN OFFICIAL DOCUMENT", font=font(16, True), anchor="mm", fill=30)
    y = 70
    for i, hl in enumerate(spec["header"].split("\n")):
        d.text((W // 2, y), hl, font=font(30 if i == 0 else 22, i == 0), anchor="mm", fill=20)
        y += 40 if i == 0 else 32
    d.line((70, y, W - 70, y), fill=30, width=3)
    y += 25
    d.text((W // 2, y + 10), spec["title"], font=font(26, True), anchor="mm", fill=20)
    y += 55
    d.text((80, y), spec["ref"], font=font(21), fill=25)
    d.text((W - 80, y), f"Date: {spec['date']}", font=font(21), anchor="ra", fill=25)
    y += 34
    if spec.get("din"):
        d.text((80, y), f"DIN: {spec['din']}", font=font(21), fill=25)
        y += 34
    y += 10
    d.text((80, y), f"To: {spec['to']}", font=font(22), fill=25)
    y += 50
    for para in spec["body"]:
        y = _wrap(d, para, 80, y, font(22), W - 160) + 12
    pos = {}
    # signature block
    sy = max(y + 30, 940)
    if spec.get("seal"):
        cx, cy = (560 if spec.get("qr_url") else 780), sy + 90
        _seal(d, cx, cy, 85, spec.get("seal_label", "SEAL"), rng)
        pos["seal"] = (cx - 90, cy - 90, cx + 90, cy + 90)
    pts = [(100 + t * 4, sy + 40 + 15 * np.sin(t / 3.0 + rng.random())) for t in range(60)]
    d.line(pts, fill=30, width=3)
    d.text((100, sy + 75), spec.get("signatory", "Authorised Officer"), font=font(20), fill=35)
    if spec.get("ds_name"):
        d.text((100, sy + 105), f"Digitally signed by {spec['ds_name']}", font=font(18), fill=35)
        d.text((100, sy + 130), f"Date: {spec['date']} 11:{rng.randint(10, 59)} IST", font=font(18), fill=35)
    if spec.get("qr_url"):
        q = qrcode.QRCode(box_size=4, border=2)
        q.add_data(spec["qr_url"])
        q.make(fit=True)
        qi = q.make_image(fill_color="black", back_color="white").convert("L")
        qi = qi.resize((170, 170), Image.NEAREST)
        img.paste(qi, (W - 260, H - 230))
        d.text((W - 260, H - 55), f"Passcode: {spec.get('passcode', '')}", font=font(18), fill=25)
    meta = {}
    im, scanmeta = scan(img, rng)
    meta.update(scanmeta)
    manip = spec.get("manip")
    if manip == "copy_move" and "seal" in pos:
        x0, y0, x1, y1 = pos["seal"]
        patch = im.crop((x0, y0, x1, y1))
        im.paste(patch, (x0 - 330, y0 + 20))
        im = jpeg(im, rng.randint(80, 92))
    elif manip == "splice":
        d2 = ImageDraw.Draw(im)
        yy = rng.randint(330, 520)
        d2.rectangle((76, yy, 924, yy + 34), fill=(252, 250, 246))
        d2.text((80, yy), rng.choice(spec["body"])[:60], font=font(22), fill=(25, 25, 25))
        im = jpeg(im, rng.randint(80, 92))
    meta["manip"] = manip
    return im, meta
