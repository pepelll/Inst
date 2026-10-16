"""UI sounds for the text only, synced to scripts/timeline.json (exported from src/config.ts).

Run:  python3 scripts/sfx.py  ->  public/sfx/arut_sfx.wav (48 kHz stereo, exactly the video length)
Character of the first version (crisp per-word clicks + an accent on the key word),
but darker: lower pitch, softened click, low-passed master. No sounds on the logo,
avatar morph, transition or light sweeps - only when text appears / leaves.
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
    "tick": 0.0,  # one click per word (caption + nick)
    "key": 0.0,  # soft accent on "YouTube" / "Twitch"
    "exit": 0.0,  # text blurring away before the transition
    "reverb": 0.0,
}

TONE = {
    "pitch": 0.55,  # click pitch multiplier vs. the first version (lower = less ringing)
    "master_lowpass": 6500,  # Hz - lower = duller overall
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


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def sine(freq, n, phase=0.0):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return np.sin(phase + 2 * np.pi * np.cumsum(f) / SR)


def noise(n):
    return RNG.standard_normal(n)


def place(sig, time_s, layer, pan=0.0, send=0.2):
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


def tick(pitch):
    """First-version UI click, darkened: softer click band, lower tone, more body."""
    n = int(0.07 * SR)
    click = bp(noise(n), 1200, 4500) * env_exp(n, 0.0022)
    click /= np.abs(click).max() + 1e-9
    tone = sine(pitch, n) * env_exp(n, 0.014, 0.0008)
    body = sine(pitch / 3.5, n) * env_exp(n, 0.016, 0.001)
    return lp(0.4 * click + 0.4 * tone + 0.3 * body, 5000)


def accent(f0):
    """Muted bell-ish accent for the key word: two soft partials, short decay, plus a tick."""
    n = int(0.45 * SR)
    out = np.zeros(n)
    for ratio, amp, dec in [(1, 1.0, 0.16), (2.76, 0.25, 0.06)]:
        out += amp * sine(f0 * ratio, n, RNG.uniform(0, 6.28)) * env_exp(n, dec, 0.003)
    out = lp(out * 0.3, 3500)
    tk = tick(f0 * 2)
    out[: len(tk)] += 0.5 * tk
    return out


def soft_whoosh(dur, f0, f1, peak=0.4):
    n = int(dur * SR)
    win, hop = 1024, 256
    w = np.hanning(win)
    src = noise(n + win)
    out = np.zeros(n + win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    frames = max(1, n // hop)
    for k in range(frames):
        fc = f0 * (f1 / f0) ** (k / frames)
        band = np.exp(-0.5 * (np.log(np.maximum(freqs, 1) / fc) / 0.5) ** 2)
        out[k * hop : k * hop + win] += np.fft.irfft(np.fft.rfft(src[k * hop : k * hop + win] * w) * band) * w
    out = lp(out[:n], 4000)
    out /= np.abs(out).max() + 1e-9
    tt = np.linspace(0, 1, n)
    e = np.where(tt < peak, (tt / peak) ** 2, ((1 - tt) / (1 - peak)) ** 1.6)
    return out * e


def reverb_ir(dur=0.9, decay=0.14):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.stack([noise(n), noise(n)], 1) * np.exp(-t / decay)[:, None]
    ir = np.stack([lp(ir[:, c], 4500) for c in range(2)], 1)
    return ir / np.sqrt((ir**2).sum(0))


# ---------------------------------------------------------------- arrange (text only)

YT, TW = tl["youtube"], tl["twitch"]
P = TONE["pitch"]
PITCH = {"youtube": [2350, 2640, 2960, 3520], "twitch": [2490, 2790, 3140, 3730]}
KEY = {"youtube": 659.3, "twitch": 784.0}  # E5 / G5

for S in (YT, TW):
    # caption: one click per word, the key word gets a soft accent
    for i, w in enumerate(S["captionWords"]):
        place(tick(PITCH[S["id"]][i % 4] * P) * 0.8, t_of(w["frame"] + 2), "tick", pan=-0.25 + 0.17 * i)
        if w["key"]:
            place(accent(KEY[S["id"]]) * 0.55, t_of(w["frame"] + 3), "key", pan=0.12, send=0.35)
    # nick: one click per word
    for i, w in enumerate(S["nickWords"]):
        place(tick(PITCH[S["id"]][3 - i] * 0.85 * P) * 0.8, t_of(w["frame"] + 2), "tick", pan=0.1 * (i * 2 - 1))

# text exit before the transition: a light swish + quick descending clicks as the words blur away
if YT["textExit"] is not None:
    E = YT["textExit"]
    place(soft_whoosh(0.26, 700, 2600) * 0.22, t_of(E), "exit", send=0.25)
    for i in range(4):
        place(tick((3600 - i * 280) * P) * 0.28, t_of(E + i * 1.5 + 1), "exit", pan=0.2 - 0.13 * i, send=0.25)

# ---------------------------------------------------------------- master
wet = hp(wet.T, 400).T
ir = reverb_ir()
rev = np.stack([fftconvolve(wet[:, c], ir[:, c])[:N] for c in range(2)], 1)
mix = dry + rev * db(GAIN["reverb"]) * 0.5
mix = lp(hp(mix.T, 40), TONE["master_lowpass"], 2).T
fade = int(0.06 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
mix = np.tanh(mix * 1.3) / 1.3
# clicks only: normalize to -3 dBFS peak so they sit like UI sounds, not a loud track
mix *= db(-3.0) / (np.abs(mix).max() + 1e-9)

os.makedirs("public/sfx", exist_ok=True)
sf.write("public/sfx/arut_sfx.wav", mix.astype(np.float32), SR, subtype="PCM_24")
print("public/sfx/arut_sfx.wav", f"{len(mix) / SR:.3f}s")
