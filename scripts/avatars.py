"""Crop round avatars from the screenshots, upscale (EDSR x4 + Lanczos) and mask to a perfect circle."""
import sys
import cv2
import numpy as np

MODEL = sys.argv[1]
OUT = 1040  # 2x the on-screen size (~520px)
SS = 4  # supersampling for an anti-aliased mask edge

JOBS = [
    # file, cx, cy, radius (inset a bit inside the real edge to drop UI anti-aliasing)
    ("youtube.jpg", 156.6, 127.8, 105.5, "public/avatar_youtube.png"),
    ("twitch.jpg", 179.5, 148.0, 130.0, "public/avatar_twitch.png"),
]

sr = cv2.dnn_superres.DnnSuperResImpl_create()
sr.readModel(MODEL)
sr.setModel("edsr", 4)

for src, cx, cy, r, dst in JOBS:
    im = cv2.imread(src)
    # sub-pixel accurate square crop around the circle
    size = int(np.ceil(2 * r)) + 2
    M = np.float32([[1, 0, size / 2 - cx], [0, 1, size / 2 - cy]])
    crop = cv2.warpAffine(im, M, (size, size), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
    up = sr.upsample(crop)
    up = cv2.resize(up, (OUT, OUT), interpolation=cv2.INTER_LANCZOS4)
    # gentle unsharp mask
    blur = cv2.GaussianBlur(up, (0, 0), 2.2)
    up = cv2.addWeighted(up, 1.35, blur, -0.35, 0)
    # anti-aliased circular alpha
    n = OUT * SS
    yy, xx = np.mgrid[0:n, 0:n]
    c = (n - 1) / 2
    rr = (OUT / 2 * (2 * r / size)) * SS
    mask = ((xx - c) ** 2 + (yy - c) ** 2 <= rr ** 2).astype(np.float32)
    mask = cv2.resize(mask, (OUT, OUT), interpolation=cv2.INTER_AREA)
    # crop to exactly the circle bounding box
    scale = OUT / size
    pad = int((size - 2 * r) / 2 * scale)
    bgra = cv2.cvtColor(up, cv2.COLOR_BGR2BGRA)
    bgra[..., 3] = (mask * 255).astype(np.uint8)
    bgra = bgra[pad:OUT - pad, pad:OUT - pad]
    bgra = cv2.resize(bgra, (OUT, OUT), interpolation=cv2.INTER_LANCZOS4)
    cv2.imwrite(dst, bgra)
    print(dst, bgra.shape)
