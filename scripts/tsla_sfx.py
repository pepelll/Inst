"""Soft, muffled SFX for the TSLA volume insert, synced to scripts/tsla_timeline.json (from src/tsla/timing.ts).

Run:  node --experimental-strip-types scripts/export-tsla-timeline.mjs && python3 -I scripts/tsla_sfx.py
  ->  public/sfx/tsla_sfx.wav (48 kHz stereo, exactly 5.5 s)
Only low sines and band-limited noise: nothing above ~3 kHz, no clicks, quiet master (-6 dBFS peak).
Tweak GAIN (dB per layer) to rebalance.
"""
import json
import os

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
RNG = np.random.default_rng(11)

GAIN = {
    "air": 0.0,  # opening swell
    "tok": 0.0,  # soft wooden taps as candles appear
    "rise": 0.0,  # volume bars rising
    "thump": 0.0,  # the volume spike
    "ghost": 0.0,  # dot shooting up and falling back
    "land": 0.0,  # dot lands / price chip
    "reverb": 0.0,
}
MASTER_LOWPASS = 3200

tl = json.load(open("scripts/tsla_timeline.json"))
FPS = tl["fps"]
N = int(round(tl["durationInFrames"] / FPS * SR))
dry = np.zeros((N, 2))
wet = np.zeros((N, 2))


def db(x):
    return 10 ** (x / 20)


def t_of(frame):
    return frame / FPS


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def sine(freq, n, phase=0.0):
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return np.sin(phase + 2 * np.pi * np.cumsum(f) / SR)


def noise(n):
    return RNG.standard_normal(n)


def env(n, attack, decay):
    t = np.arange(n) / SR
    return np.clip(t / max(attack, 1e-4), 0, 1) ** 2 * np.exp(-np.maximum(t - attack, 0) / decay)


def swell_env(n, peak):
    tt = np.linspace(0, 1, n)
    return np.where(tt < peak, np.sin(0.5 * np.pi * tt / peak) ** 2, np.cos(0.5 * np.pi * (tt - peak) / (1 - peak)) ** 2)


def place(sig, time_s, layer, pan=0.0, send=0.3):
    if sig.ndim == 1:
        ang = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(ang), sig * np.sin(ang)], 1)
    i0 = int(round(time_s * SR))
    sig = sig[: N - i0] * db(GAIN[layer])
    dry[i0 : i0 + len(sig)] += sig
    wet[i0 : i0 + len(sig)] += sig * send


# ---------------------------------------------------------------- sound designs


def air(dur):
    """Dark breathy swell with a low hum underneath."""
    n = int(dur * SR)
    a = lp(bp(noise(n), 120, 900), 700) * 0.5
    hum = sine(55, n) * 0.35 + sine(82.4, n) * 0.18
    return (a / (np.abs(a).max() + 1e-9) * 0.5 + hum) * swell_env(n, 0.45)


def tok(f0):
    """Muted wooden tap: a low sine with a fast pitch drop, no transient click."""
    n = int(0.22 * SR)
    f = f0 * (1 + 0.5 * np.exp(-np.arange(n) / SR / 0.008))
    body = sine(f, n) * env(n, 0.004, 0.05)
    felt = lp(noise(n), 900) * env(n, 0.003, 0.012) * 0.25
    return lp(body + felt, 1800)


def rise(dur, f0, f1):
    """Soft low-passed air moving upwards."""
    n = int(dur * SR)
    src = noise(n)
    out = np.zeros(n)
    hop = 2400
    for k in range(0, n, hop):
        fc = f0 * (f1 / f0) ** (k / n)
        seg = src[k : k + hop * 2]
        out[k : k + len(seg)] += bp(seg, fc * 0.6, fc * 1.4) * np.hanning(len(seg))
    out = lp(out, 2200)
    return out / (np.abs(out).max() + 1e-9) * swell_env(n, 0.7)


def thump():
    """Deep soft sub hit with a warm bloom (no attack click)."""
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 48 + 40 * np.exp(-t / 0.05)
    sub = sine(f, n) * env(n, 0.012, 0.32)
    bloom = np.zeros(n)
    for fr, amp in [(110, 0.3), (164.8, 0.2), (220, 0.12), (329.6, 0.06)]:
        bloom += amp * sine(fr * (1 + 0.003 * RNG.standard_normal()), n, RNG.uniform(0, 6.28))
    bloom *= swell_env(n, 0.18) * np.exp(-t / 0.8)
    breath = lp(noise(n), 500) * env(n, 0.03, 0.18) * 0.12
    return lp(sub * 0.9 + bloom + breath, 1500)


def ghost_up(dur):
    """Gentle rising tone that runs out of energy at the apex."""
    n = int(dur * SR)
    tt = np.linspace(0, 1, n)
    f = 180 + 260 * (1 - (1 - tt) ** 2)
    tone = sine(f, n) * 0.5 + sine(f * 1.5, n) * 0.12
    return lp(tone, 1400) * swell_env(n, 0.75) * 0.8


def ghost_fall(dur):
    n = int(dur * SR)
    tt = np.linspace(0, 1, n)
    f = 420 * (1 - 0.65 * tt**2)
    return lp(sine(f, n) * 0.4, 1000) * swell_env(n, 0.2) * 0.6


def land():
    """Low soft 'tup' when the dot lands on the real close."""
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = 70 + 50 * np.exp(-t / 0.03)
    return lp(sine(f, n) * env(n, 0.006, 0.14) + 0.25 * sine(196, n) * env(n, 0.01, 0.2), 1200)


def reverb_ir(dur=1.4, decay=0.32):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.stack([noise(n), noise(n)], 1) * np.exp(-t / decay)[:, None]
    ir = np.stack([lp(ir[:, c], 2500) for c in range(2)], 1)
    return ir / np.sqrt((ir**2).sum(0))


# ---------------------------------------------------------------- arrange

place(air(1.4) * 0.35, 0.0, "air", send=0.4)

# a few soft taps (not one per candle: every other one, getting slightly brighter)
for j, i in enumerate(range(0, tl["bars"] - 1, 2)):
    fr = tl["candlesIn"] + i * tl["candleStagger"] + 3
    place(tok(150 + 18 * j) * 0.22, t_of(fr), "tok", pan=-0.5 + 0.25 * j, send=0.35)

place(rise(0.75, 200, 900) * 0.16, t_of(tl["volumesIn"] - 4), "rise", send=0.35)

place(thump() * 0.8, t_of(tl["spike"] + 2), "thump", pan=0.15, send=0.45)
place(rise(0.35, 300, 1200) * 0.08, t_of(tl["spike"] - 14), "thump", pan=0.15)

up_dur = t_of(tl["ghostApex"] - tl["ghostLaunch"] + 6)
place(ghost_up(up_dur) * 0.22, t_of(tl["ghostLaunch"]), "ghost", pan=0.25, send=0.5)
place(ghost_fall(t_of(tl["land"] - tl["fallStart"] + 4)) * 0.18, t_of(tl["fallStart"]), "ghost", pan=0.25, send=0.5)

place(land() * 0.55, t_of(tl["land"]), "land", pan=0.2, send=0.45)
place(tok(196) * 0.12, t_of(tl["priceChip"] + 6), "land", pan=0.2, send=0.5)

# ---------------------------------------------------------------- master
ir = reverb_ir()
rev = np.stack([fftconvolve(hp(wet[:, c], 120), ir[:, c])[:N] for c in range(2)], 1)
mix = dry + rev * db(GAIN["reverb"]) * 0.45
mix = lp(hp(mix.T, 30), MASTER_LOWPASS, 2).T
fade = int(0.25 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
mix = np.tanh(mix * 1.2) / 1.2
mix *= db(-6.0) / (np.abs(mix).max() + 1e-9)

os.makedirs("public/sfx", exist_ok=True)
sf.write("public/sfx/tsla_sfx.wav", mix.astype(np.float32), SR, subtype="PCM_24")
print("public/sfx/tsla_sfx.wav", f"{len(mix) / SR:.3f}s")
