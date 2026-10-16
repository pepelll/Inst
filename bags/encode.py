"""Composite the transparent Cycles frames (bags + shadow-catcher shadows) over a seamless grey studio gradient
and encode H.264.  Run: python3 -I encode.py [render_dir] [out.mp4]
"""
import glob
import os
import subprocess
import sys

import numpy as np
from PIL import Image


def backdrop(w, h):
    """Neutral light grey, softly brighter in the centre (sRGB 0..1). One field for wall and floor: no horizon."""
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (x / w - 0.5) / 0.62
    ny = (y / h - 0.44) / 0.58
    r = np.clip(np.sqrt(nx**2 + ny**2), 0, 1.6)
    t = np.clip(r, 0, 1) ** 1.6
    v = 0.86 - 0.21 * t
    v = v - 0.03 * np.clip(y / h - 0.6, 0, 1)  # floor a touch darker towards the camera
    rng = np.random.default_rng(3)
    v = v + (rng.random((h, w)) - 0.5) / 255  # dither: no banding
    rgb = np.stack([v * 0.995, v * 0.997, v * 1.005], -1)
    return rgb.astype(np.float32)


def composite(path, bg):
    im = np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255
    a = im[..., 3:4]
    return (np.clip(im[..., :3] * a + bg * (1 - a), 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "render"
    out = sys.argv[2] if len(sys.argv) > 2 else "../out/tesla_bags_drop.mp4"
    files = sorted(glob.glob(os.path.join(src, "frame_*.png")))
    w, h = Image.open(files[0]).size
    bg = backdrop(w, h)
    cmd = [
        "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", "60", "-i", "-",
        "-vf", "scale=1920:1080:flags=lanczos", "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out,
    ]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in files:
        p.stdin.write(composite(f, bg).tobytes())
    p.stdin.close()
    p.wait()
    print(out, len(files), "frames")
