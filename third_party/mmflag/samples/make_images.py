"""Generate synthetic 'official notice' images: authentic scans and three tampering types.

All organisations, names and numbers are fictitious (Office of the Sample Authority).
Authentic pipeline : render -> mild optical blur -> scan/sensor noise -> JPEG.
Tampered pipelines (applied to an authentic scan, then re-saved as JPEG):
  splice_clean  : a text line (name/amount/case no.) blanked and re-typed digitally (no scan noise)
  splice_foreign: a patch taken from a *different* scan (other noise level + heavy prior JPEG)
  copy_move     : the seal cloned onto a second location in the same document
"""
from __future__ import annotations

import io
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
W, H = 1000, 1300
NAMES = ["A. Kumar", "S. Priya", "R. Menon", "M. Iqbal", "J. Thomas", "K. Lakshmi", "V. Rao", "P. Das"]


def _font(sz, bold=False):
    return ImageFont.truetype(FONT_B if bold else FONT, sz)


def render_notice(rng: random.Random):
    img = Image.new("L", (W, H), 250)
    d = ImageDraw.Draw(img)
    d.text((W // 2, 70), "OFFICE OF THE SAMPLE AUTHORITY", font=_font(36, True), anchor="mm", fill=20)
    d.text((W // 2, 115), "(Fictitious notice generated for detector testing)", font=_font(18), anchor="mm", fill=60)
    d.line((80, 145, W - 80, 145), fill=30, width=3)
    case = f"Ref. No. SA/{rng.randint(1000, 9999)}/{rng.randint(2020, 2026)}"
    name = rng.choice(NAMES)
    amt = f"Rs. {rng.randint(10, 99)},{rng.randint(100, 999)}/-"
    lines = [case, f"Date: {rng.randint(1, 28):02d}-{rng.randint(1, 12):02d}-2026", "",
             f"To: {name}", "",
             "Subject: Intimation regarding pending verification", "",
             "This is to inform you that the verification of your records",
             "is pending with this office. You are requested to appear in",
             "person with original documents at the address below during",
             "working hours. No payment is collected over phone or video",
             "call by this office under any circumstances.", "",
             f"Processing fee (payable only at counter): {amt}", "",
             "Address: Block C, Example Complex, Sample Nagar."]
    y = 190
    pos = {}
    for ln in lines:
        if ln:
            d.text((100, y), ln, font=_font(24), fill=25)
            if ln.startswith("To:"):
                pos["name"] = (100, y)
            if ln.startswith("Processing"):
                pos["amount"] = (100, y)
            if ln.startswith("Ref."):
                pos["case"] = (100, y)
        y += 38
    # seal: textured concentric rings + radial pattern
    cx, cy, r = rng.randint(620, 760), rng.randint(960, 1060), 95
    for k, rr in enumerate(range(r, 30, -9)):
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), outline=60 + (k % 3) * 25, width=3)
    for a in np.linspace(0, 2 * np.pi, 36, endpoint=False):
        d.line((cx + 35 * np.cos(a), cy + 35 * np.sin(a), cx + (60 + 8 * (a % 1)) * np.cos(a), cy + 60 * np.sin(a)), fill=70, width=2)
    d.text((cx, cy), "SA", font=_font(30, True), anchor="mm", fill=40)
    # signature squiggle
    sx, sy = 140, 1080
    pts = [(sx + t * 4, sy + 18 * np.sin(t / 3.0 + rng.random()) + rng.uniform(-3, 3)) for t in range(70)]
    d.line(pts, fill=30, width=3)
    d.text((140, 1130), "Authorised Signatory", font=_font(22), fill=40)
    pos["seal"] = (cx - r - 5, cy - r - 5, cx + r + 5, cy + r + 5)
    return img, pos


def scan(img: Image.Image, rng: random.Random, sigma=None, q=None) -> tuple[Image.Image, dict]:
    sigma = sigma if sigma is not None else rng.uniform(2.5, 6.0)
    q = q if q is not None else rng.randint(78, 92)
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(0.7)), np.float32)
    nr = np.random.default_rng(rng.randint(0, 2**31))
    yy, xx = np.mgrid[0:a.shape[0], 0:a.shape[1]]
    vign = 1 - 0.06 * (((xx - a.shape[1] / 2) / a.shape[1]) ** 2 + ((yy - a.shape[0] / 2) / a.shape[0]) ** 2)
    a = a * vign + nr.normal(0, sigma, a.shape)
    rgb = np.stack([a + 2, a, a - 4], -1)  # slight paper tint
    out = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8))
    return jpeg(out, q), {"sigma": round(sigma, 2), "q": q}


def jpeg(img: Image.Image, q: int) -> Image.Image:
    b = io.BytesIO()
    img.save(b, "JPEG", quality=q)
    return Image.open(io.BytesIO(b.getvalue())).convert("RGB")


def tamper(kind: str, rng: random.Random):
    base, pos = render_notice(rng)
    scanned, meta = scan(base, rng)
    im = scanned.copy()
    d = ImageDraw.Draw(im)
    if kind == "splice_clean":
        field = rng.choice(["name", "amount", "case"])
        x, y = pos[field]
        d.rectangle((x - 6, y - 6, x + 820, y + 34), fill=(252, 250, 246))
        new = {"name": f"To: {rng.choice(NAMES)} (Accused)",
               "amount": f"Security deposit (transfer via UPI): Rs. {rng.randint(1, 9)},{rng.randint(10, 99)},000/-",
               "case": f"Ref. No. SA/CR/{rng.randint(1000, 9999)}/ARREST"}[field]
        d.text((x, y), new, font=_font(24), fill=(25, 25, 25))
        region = (x - 6, y - 6, x + 820, y + 34)
    elif kind == "splice_foreign":
        other, _ = render_notice(random.Random(rng.random()))
        other_s, _ = scan(other, rng, sigma=rng.uniform(9, 14), q=rng.randint(45, 60))
        field = rng.choice(["name", "amount", "case"])
        x, y = pos[field]
        box = (x - 6, y - 40, x + 640, y + 75)
        im.paste(other_s.crop(box), box[:2])
        region = box
    elif kind == "copy_move":
        x0, y0, x1, y1 = pos["seal"]
        patch = scanned.crop((x0, y0, x1, y1))
        tx, ty = rng.randint(330, 420), rng.randint(1000, 1080)
        im.paste(patch, (tx, ty))
        region = (tx, ty, tx + (x1 - x0), ty + (y1 - y0))
    else:
        raise ValueError(kind)
    im = jpeg(im, rng.randint(78, 92))
    return im, {"kind": kind, "region_xyxy": [int(v) for v in region], **meta}


def authentic(rng: random.Random):
    base, _ = render_notice(rng)
    im, meta = scan(base, rng)
    if rng.random() < 0.5:  # benign re-save (e.g. forwarded on a messaging app)
        im = jpeg(im, rng.randint(70, 85))
        meta["resaved"] = True
    return im, {"kind": "authentic", **meta}
