"""Split the source PNG into body / handle masks and make a back-side texture without the logo.
Run: python3 -I prep_textures.py  (writes tex/front.png, tex/back.png, tex/body_mask.png, tex/handle_mask.png)
"""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src = Image.open("tex/bag_src.png").convert("RGBA")
im = np.array(src)
a = im[..., 3] > 128

# body = big shape without the thin handle; handle = the large thin components removed by opening
yy, xx = np.mgrid[-40:41, -40:41]
disk = xx**2 + yy**2 <= 40**2
opened = ndi.binary_opening(a, structure=disk)
rest = a & ~opened
lab, n = ndi.label(rest)
sizes = ndi.sum(rest, lab, range(1, n + 1))
handle = np.zeros_like(a)
for k, s in enumerate(sizes, 1):
    ys, xs = np.where(lab == k)
    if s > 1500 and xs.mean() > 350 and xs.mean() < 900 and ys.mean() < 470:
        handle |= lab == k
body = a & ~handle
body = ndi.binary_opening(body, structure=np.ones((5, 5)))
body = ndi.binary_fill_holes(body)
body[:470, 1165:] = False  # zipper pull: printed on the texture, not a separate lump
body[:450, :70] = False
# keep only the largest body component
lab, n = ndi.label(body)
body = lab == (np.argmax(ndi.sum(body, lab, range(1, n + 1))) + 1)
Image.fromarray((body * 255).astype(np.uint8)).save("tex/body_mask.png")
Image.fromarray((handle * 255).astype(np.uint8)).save("tex/handle_mask.png")

rgb = im[..., :3].astype(np.float32)
# fill transparent areas with edge colors so texture filtering at the silhouette never pulls in black/garbage
idx = ndi.distance_transform_edt(~a, return_distances=False, return_indices=True)
rgb = rgb[idx[0], idx[1]]
Image.fromarray(rgb.astype(np.uint8)).save("tex/front.png")

# back: replace the logo (between the straps) with plain leather: high-frequency grain copied from below,
# low-frequency shading interpolated from the surroundings (normalized convolution), so no visible patch
back = rgb.copy()
x0, x1, y0, y1 = 520, 735, 560, 745
dy = 200
hole = np.zeros(a.shape, np.float32)
hole[y0:y1, x0:x1] = 1
sig = 40
valid = (1 - hole) * (rgb.mean(-1) > 60) * a  # ignore the black straps and background
w = ndi.gaussian_filter(valid, sig)
low = np.stack([ndi.gaussian_filter(rgb[..., c] * valid, sig) for c in range(3)], -1) / np.maximum(w, 1e-4)[..., None]
patch = rgb[y0 + dy : y1 + dy, x0:x1]
patch_hi = patch - np.stack([ndi.gaussian_filter(patch[..., c], 20) for c in range(3)], -1)
fill = low[y0:y1, x0:x1] + patch_hi
m = np.zeros((y1 - y0, x1 - x0), np.float32)
m[14:-14, 14:-14] = 1
m = ndi.gaussian_filter(m, 6)
back[y0:y1, x0:x1] = back[y0:y1, x0:x1] * (1 - m[..., None]) + fill * m[..., None]
back = np.clip(back, 0, 255)
Image.fromarray(back.astype(np.uint8)).save("tex/back.png")
print("body px", body.sum(), "handle px", handle.sum())

# plain grained leather (left panel, between the end and the strap) for faces the front photo cannot cover
plain = rgb[540:800, 150:410]
plain = plain - plain.mean((0, 1)) + rgb[540:800, 150:410].reshape(-1, 3).mean(0)
Image.fromarray(np.clip(plain, 0, 255).astype(np.uint8)).save("tex/plain.png")

# 1D strap mask (by photo column): lets the black straps continue over the top/bottom where the grain is used
lum = rgb[620:960].mean(-1)
dark = (lum < 50).mean(0)
dark = (dark > 0.6).astype(np.float32)
dark[:300] = 0
dark[950:] = 0  # only the two straps, not the dark end panels
dark = ndi.uniform_filter1d(dark, 5)
Image.fromarray(np.tile((dark * 255).astype(np.uint8), (8, 1))).save("tex/strap_mask.png")
print("strap columns", np.where(dark > 0.5)[0][[0, -1]])
