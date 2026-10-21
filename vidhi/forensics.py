"""Forensic tool agent: wraps the training-free mmflag detector, with a result cache."""
from __future__ import annotations

import sys

from vidhi.paths import MMFLAG_PATH, add  # noqa: E402
add(MMFLAG_PATH)
from mmflag.audio import analyze_audio  # noqa: E402
from mmflag.image import analyze_image  # noqa: E402
from mmflag.video import analyze_video  # noqa: E402

_CACHE: dict = {}


def score(kind: str, key: str, obj):
    """kind in {image, audio, video}; obj = PIL image, waveform array, or video path."""
    k = (kind, key)
    if k not in _CACHE:
        fn = {"image": analyze_image, "audio": analyze_audio, "video": analyze_video}[kind]
        r = fn(obj)
        _CACHE[k] = (r["confidence_manipulated"], max(r["cues"].items(), key=lambda kv: kv[1]["p"])[0])
    return _CACHE[k]


def preload(cache: dict):
    _CACHE.update(cache)
