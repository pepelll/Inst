"""Random search over drop poses: runs build.py --sim-only in parallel and scores the final pile.
Run: python3 -I search_drops.py N  -> prints the best DROPS list (paste into build.py)."""
import concurrent.futures as cf
import json
import math
import os
import random
import subprocess
import sys

import numpy as np

BASE = [
    (1, (-0.04, 0.03, 0.72), (6, -5, 12)),
    (14, (0.14, 0.02, 1.62), (-10, 8, -18)),
    (42, (-0.02, -0.04, 1.75), (8, 5, 10)),
]
CAM = np.array([0.12, -2.85, 1.12])


def rotate(q, v):
    w, x, y, z = q
    u = np.array([x, y, z])
    v = np.asarray(v, float)
    return v + 2 * np.cross(u, np.cross(u, v) + w * v)


def score(traj):
    names = sorted(traj)
    s = 0.0
    fin = {n: np.array(traj[n][125]) for n in names}
    pos = np.array([fin[n][:3] for n in names])
    for n in names:
        p, q = fin[n][:3], fin[n][3:]
        if abs(p[0]) > 0.33 or p[1] < -0.35 or p[1] > 0.4:
            s -= 6
        front = rotate(q, (0, -1, 0))
        length = rotate(q, (1, 0, 0))
        to_cam = (CAM - p) / np.linalg.norm(CAM - p)
        s += 2.0 * max(0, front @ to_cam)  # logo visible
        if abs(length[2]) > 0.55:
            s -= 5  # standing on an end looks odd
    for a_ in range(len(names)):
        for b_ in range(a_ + 1, len(names)):
            d = pos[a_] - pos[b_]
            if abs(d[0]) < 0.18 and abs(d[2]) < 0.12:
                s -= 3  # one bag hidden behind another
    s -= 6 * np.mean(np.linalg.norm(pos[:, :2] - pos[:, :2].mean(0), axis=1))
    top = [fin[n][2] for n in names]
    s += 2.0 * (max(top) > 0.22) + 1.0 * (fin[names[-1]][2] > 0.22)
    # visible but calm settle: still moving a bit is fine, flying is not
    v = np.array([np.linalg.norm(np.array(traj[n][125][:3]) - np.array(traj[n][119][:3])) * 10 for n in names])
    s -= 3 * np.clip(v - 0.25, 0, None).sum()
    return s


def run(i, drops):
    env = dict(os.environ, DROPS=json.dumps(drops), TRAJ=f"/tmp/claude-0/traj_{i}.txt")
    subprocess.run([sys.executable, "build.py", "--sim-only"], env=env, capture_output=True)
    return json.load(open(f"/tmp/claude-0/traj_{i}.txt.json"))


def perturb(rng):
    out = []
    for k, (rel, loc, rot) in enumerate(BASE):
        if k == 0:
            out.append((rel, loc, tuple(r + rng.uniform(-6, 6) for r in rot)))
            continue
        out.append((rel, (loc[0] + rng.uniform(-0.1, 0.1), loc[1] + rng.uniform(-0.1, 0.1), loc[2]),
                    tuple(r + rng.uniform(-18, 18) for r in rot)))
    return out


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    rng = random.Random(1)
    cands = [BASE] + [perturb(rng) for _ in range(n - 1)]
    results = []
    with cf.ThreadPoolExecutor(4) as ex:
        futs = {ex.submit(run, i, c): c for i, c in enumerate(cands)}
        for f in cf.as_completed(futs):
            c = futs[f]
            try:
                results.append((score(f.result()), c))
            except Exception as e:  # noqa: BLE001
                print("fail", e)
    results.sort(key=lambda r: -r[0])
    for sc_, c in results[:5]:
        print(f"{sc_:.2f}", json.dumps([[r, [round(v, 3) for v in l], [round(v, 1) for v in o]] for r, l, o in c]))
