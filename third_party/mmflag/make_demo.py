"""Write a small demo set of sample media to demo/ (one of each kind)."""
import os, random, zlib
import numpy as np
from scipy.io import wavfile
from samples import make_images as MI, make_audio as MA
from samples.make_video import render

os.makedirs("demo", exist_ok=True)
s = lambda k: zlib.crc32(("demo-" + k).encode())
im, _ = MI.authentic(random.Random(s("a"))); im.save("demo/notice_authentic.jpg", quality=88)
for k in ("splice_clean", "splice_foreign", "copy_move"):
    im, m = MI.tamper(k, random.Random(s(k))); im.save(f"demo/notice_{k}.jpg", quality=88)
    print(k, m["region_xyxy"])
rng = np.random.default_rng(s("aa"))
x, m = MA.authentic(rng)
while m["kind"] != "authentic":
    x, m = MA.authentic(rng)
wavfile.write("demo/call_authentic.wav", MA.SR, x)
x, m = MA.splice(np.random.default_rng(s("sp"))); wavfile.write("demo/call_splice.wav", MA.SR, x); print("splice", m)
x, m = MA.synthetic_voice(np.random.default_rng(s("sv"))); wavfile.write("demo/call_synthetic_voice.wav", MA.SR, x); print("synthetic", m)
for k in ("authentic", "face_swap", "splice"):
    _, m = render(np.random.default_rng(s("v" + k)), k, f"demo/statement_{k}.mp4"); print(k, m)
