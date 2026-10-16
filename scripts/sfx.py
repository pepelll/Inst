"""Procedural UI sounds / SFX for the promo, synced to scripts/timeline.json (exported from src/config.ts).

Run:  python3 scripts/sfx.py  ->  public/sfx/arut_sfx.wav (48 kHz stereo, exactly the video length)
Sound palette follows the opening of the reference: soft, muted "plop/thock" taps
(a fast downward pitch drop into a short low-mid body) - no bells, no sparkles.
Tweak GAIN (dB per layer) and TONE to rebalance.
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
RNG = np.random.default_rng(7)

# Per-layer levels in dB (0 = as designed). Set a layer to -120 to mute it.
GAIN = {
    "tap": 0.0,  # word appear taps
    "thud": 0.0,  # logo / avatar arrivals
    "whoosh": 0.0,  # morph + transition air
    "impact": 0.0,  # circle reveal hit
    "atmos": 0.0,  # very quiet sub bed
    "reverb": 0.0,  # small dark room
}

TONE = {
    "master_lowpass": 3800,  # Hz - lower = duller overall
    "tap_from": 1900,  # Hz - where the tap pitch drop starts
    "tap_to": 560,  # Hz - where it lands (the "body" of the tap)
}

tl = json.load(open("scripts/timeline.json"))
FPS = tl["fps"]
N = int(round(tl["durationInFrames"] / FPS * SR))
dry = np.zeros((N, 2))
wet = np.zeros((N, 2))


def db(x):
    return 10 ** (x / 20)


def t_of(frame):
    return frame / FPS


def env_exp(n, decay_s, attack_s=0.001):
    t = np.arange(n) / SR
    return np.clip(t / max(attack_s, 1e-5), 0, 1) * np.exp(-t / decay_s)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def sine(freq, n):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return np.sin(2 * np.pi * np.cumsum(f) / SR)


def noise(n):
    return RNG.standard_normal(n)


def place(sig, time_s, layer, pan=0.0, send=0.15):
    if sig.ndim == 1:
        ang = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(ang), sig * np.sin(ang)], 1)
    i0 = int(round(time_s * SR))
    if i0 < 0:
        sig, i0 = sig[-i0:], 0
    sig = sig[: N - i0] * db(GAIN[layer])
    dry[i0 : i0 + len(sig)] += sig
    wet[i0 : i0 + len(sig)] += sig * send


# ---------------------------------------------------------------- sound designs


def tap(scale=1.0, decay=0.05):
    """Muted 'plop' tap from the reference: pitch drops fast into a short low-mid body + tiny sub."""
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    f_hi, f_lo = TONE["tap_from"] * scale, TONE["tap_to"] * scale
    f = f_lo + (f_hi - f_lo) * np.exp(-t / 0.007)
    body = sine(f, n) * env_exp(n, decay, 0.0015)
    sub = sine(55 + 140 * np.exp(-t / 0.01), n) * env_exp(n, 0.035, 0.002)
    x = body * 0.8 + sub * 0.45
    return lp(x, 2400 * scale, 2)


def thud(scale=0.6):
    """Deeper, rounder version of the tap for logo / avatar arrivals."""
    n = int(0.3 * SR)
    t = np.arange(n) / SR
    x = tap(scale, decay=0.07)
    x = np.pad(x, (0, n - len(x)))
    sub = sine(42 + 70 * np.exp(-t / 0.03), n) * env_exp(n, 0.09, 0.003)
    return lp(x * 0.9 + sub * 0.5, 1600, 2)


def soft_whoosh(dur, f0, f1, peak=0.6):
    """Dark, filtered air move (band glides f0 -> f1, everything kept under ~2 kHz)."""
    n = int(dur * SR)
    win, hop = 1024, 256
    w = np.hanning(win)
    src = noise(n + win)
    out = np.zeros(n + win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    frames = max(1, n // hop)
    for k in range(frames):
        fc = f0 * (f1 / f0) ** (k / frames)
        band = np.exp(-0.5 * (np.log(np.maximum(freqs, 1) / fc) / 0.6) ** 2)
        out[k * hop : k * hop + win] += np.fft.irfft(np.fft.rfft(src[k * hop : k * hop + win] * w) * band) * w
    out = lp(out[:n], 2200, 2)
    out /= np.abs(out).max() + 1e-9
    tt = np.linspace(0, 1, n)
    e = np.where(tt < peak, np.sin(np.pi / 2 * tt / peak) ** 2, np.cos(np.pi / 2 * (tt - peak) / (1 - peak)) ** 2)
    return out * e


def dark_impact(dur=0.9):
    """Muffled hit: sub drop + low thump, no crack or air."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    sub = sine(36 + 50 * np.exp(-t / 0.05), n) * env_exp(n, 0.2, 0.003)
    body = lp(noise(n), 500, 2) * env_exp(n, 0.04, 0.002)
    body /= np.abs(body).max() + 1e-9
    x = sub + 0.35 * body + 0.5 * np.pad(thud(0.45), (0, max(0, n - int(0.3 * SR))))[:n]
    return np.tanh(x * 1.3) / np.tanh(1.3)


def reverb_ir(dur=0.6, decay=0.09):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.stack([noise(n), noise(n)], 1) * np.exp(-t / decay)[:, None]
    ir = np.stack([lp(ir[:, c], 2500) for c in range(2)], 1)
    return ir / np.sqrt((ir**2).sum(0))


# ---------------------------------------------------------------- arrange

YT, TW, TR = tl["youtube"], tl["twitch"], tl["transition"]
# small pitch variation per word, like the reference (no melody, just life)
WORD_SCALE = [1.0, 0.94, 1.06, 0.9]

for S in (YT, TW):
    L, M = S["logoIn"], S["morph"]
    place(thud(0.62) * 0.9, t_of(L + 4), "thud", send=0.12)

    for i, w in enumerate(S["captionWords"]):
        place(tap(WORD_SCALE[i % 4]) * 0.7, t_of(w["frame"] + 2), "tap", pan=-0.15 + 0.1 * i)

    # morph: one soft air move + a rounder thud as the avatar lands
    place(soft_whoosh(0.32, 250, 1100, 0.55) * 0.22, t_of(M) - 0.04, "whoosh", send=0.1)
    place(thud(0.55) * 0.8, t_of(M + 8), "thud", send=0.12)

    # nick: a single tap on the first word only
    place(tap(0.82) * 0.65, t_of(S["nickWords"][0]["frame"] + 2), "tap")

# ---- transition: muted suck-in, soft expand, dark hit
C = YT["collapse"]
place(soft_whoosh(t_of(TR["dotStart"] - C + 6), 200, 1400, 0.85) * 0.28, t_of(C - 6), "whoosh", send=0.1)
e0, e1 = TR["expand"]
place(soft_whoosh(t_of(e1 - e0) + 0.3, 900, 180, 0.3) * 0.32, t_of(e0) - 0.03, "whoosh", send=0.12)
place(dark_impact() * 0.85, t_of(TR["flashPeak"] - 1), "impact", send=0.1)

# ---- atmos: barely-there sub bed, ducked under the hit
t = np.arange(N) / SR
sw = t_of(TR["auroraSwitch"])
bed = lp(sine(np.where(t < sw, 55.0, 61.7), N), 150) * 0.02
bed *= np.clip(t / 0.4, 0, 1) * (1 - 0.8 * np.exp(-(((t - t_of(TR["flashPeak"])) / 0.08) ** 2)))
place(bed, 0, "atmos", send=0.0)

# ---------------------------------------------------------------- master
wet = hp(wet.T, 300).T
ir = reverb_ir()
rev = np.stack([fftconvolve(wet[:, c], ir[:, c])[:N] for c in range(2)], 1)
mix = dry + rev * db(GAIN["reverb"]) * 0.5
mix = lp(hp(mix.T, 28), TONE["master_lowpass"], 2).T  # dull the top end
fade = int(0.06 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
mix = np.tanh(mix * 1.4) / 1.4
mix *= db(-1.0) / (np.abs(mix).max() + 1e-9)

os.makedirs("public/sfx", exist_ok=True)
sf.write("public/sfx/arut_sfx.wav", mix.astype(np.float32), SR, subtype="PCM_24")
print("public/sfx/arut_sfx.wav", f"{len(mix) / SR:.3f}s")
