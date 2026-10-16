"""Contact sheet of composited stills: python3 -I sheet.py out.png file1.png file2.png ..."""
import sys

import numpy as np
from PIL import Image

from encode import backdrop, composite

files = sys.argv[2:]
w, h = Image.open(files[0]).size
bg = backdrop(w, h)
cols = 2 if len(files) > 1 else 1
rows = (len(files) + cols - 1) // cols
o = Image.new("RGB", (w * cols, h * rows))
for i, f in enumerate(files):
    o.paste(Image.fromarray(composite(f, bg)), ((i % cols) * w, (i // cols) * h))
o.save(sys.argv[1])
