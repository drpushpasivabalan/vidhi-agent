"""mmflag - lightweight, training-free flagger for manipulated images, audio and video.

    from mmflag import analyze
    report = analyze("notice.jpg")          # dict with confidence_manipulated in [0,1]
"""
from __future__ import annotations

import os

IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
AUDIO_EXT = {".wav", ".mp3", ".m4a", ".aac", ".ogg", ".opus", ".flac", ".amr"}
VIDEO_EXT = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".3gp"}

__version__ = "0.1.0"


def analyze(path: str, heatmap_path: str | None = None) -> dict:
    ext = os.path.splitext(path)[1].lower()
    if ext in IMAGE_EXT:
        from .image import analyze_image
        r = analyze_image(path, heatmap_path=heatmap_path)
    elif ext in AUDIO_EXT:
        from .audio import analyze_audio
        r = analyze_audio(path)
    elif ext in VIDEO_EXT:
        from .video import analyze_video
        r = analyze_video(path)
    else:
        raise ValueError(f"unsupported file type: {ext}")
    r["file"] = os.path.basename(path)
    return r
