"""Document perception tools: OCR text, QR payload, seal presence, digital-signature line."""
from __future__ import annotations

import re

import cv2
import numpy as np
import pytesseract
from PIL import Image


def ocr(img: Image.Image) -> str:
    g = np.asarray(img.convert("L"))
    g = cv2.resize(g, None, fx=0.8, fy=0.8, interpolation=cv2.INTER_AREA)
    txt = pytesseract.image_to_string(Image.fromarray(g), config="--psm 4")
    txt = re.sub(r"SYNTHETIC RESEARCH SAMPLE.*?DOCUMENT", " ", txt, flags=re.I | re.S)
    return txt


def qr(img: Image.Image):
    g = np.asarray(img.convert("L"))
    det = cv2.QRCodeDetector()
    data = None
    try:
        data, pts, _ = det.detectAndDecode(g)
    except cv2.error:
        data = None
    if not data:  # retry on a binarised crop of the lower-right quadrant
        h, w = g.shape
        crop = g[h // 2:, w // 2:]
        _, b = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        try:
            data, pts, _ = det.detectAndDecode(b)
        except cv2.error:
            data = None
    return data or None


def seal(img: Image.Image) -> bool:
    """Concentric-ring stamp detector (Hough circles with >= 3 concentric hits)."""
    g = np.asarray(img.convert("L"))
    g = cv2.medianBlur(g, 5)
    c = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, dp=1.2, minDist=4, param1=80, param2=40, minRadius=30, maxRadius=110)
    if c is None:
        return False
    raw = np.asarray(img.convert("L")).astype(np.float32)
    h, w = raw.shape
    ang = np.linspace(0, 2 * np.pi, 180, endpoint=False)
    def n_rings(x, y):
        rings, prev = 0, False
        for r in range(24, 100):
            xs = np.clip((x + r * np.cos(ang)).astype(int), 0, w - 1)
            ys = np.clip((y + r * np.sin(ang)).astype(int), 0, h - 1)
            on = np.mean(raw[ys, xs] < 140) > 0.6
            rings += on and not prev
            prev = on
        return rings

    for x, y, _ in c[0][:80]:
        # verify: a stamp has several *complete* dark rings around one centre
        for dx in (-3, 0, 3):
            for dy in (-3, 0, 3):
                if n_rings(x + dx, y + dy) >= 3:
                    return True
    return False


def perceive(img: Image.Image) -> dict:
    text = ocr(img)
    payload = qr(img)
    return {
        "text": text,
        "qr": payload,
        "seal": seal(img),
        "digital_signature": bool(re.search(r"digitally\s+sign", text, re.I)),
    }
