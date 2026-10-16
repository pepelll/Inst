"""Procedural UI sounds / SFX for the promo, synced to scripts/timeline.json (exported from src/config.ts).

Run:  python3 scripts/sfx.py  ->  public/sfx/arut_sfx.wav (48 kHz stereo, exactly the video length)
All sounds are synthesized here (no samples). Tweak GAIN (dB per layer) to rebalance the mix.
"""
import json
import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 48000
RNG = np.random.default_rng(7)

# Per-layer levels in dB (0 = as designed). Set a layer to -120 to mute it.
GAIN = {
    "tick": 0.0,  # word appear clicks
    "key": 0.0,  # bell on the highlighted word
    "pop": 0.0,  # logo / avatar pops
    "whoosh": 0.0,  # moves, morphs, text exit
    "sheen": 0.0,  # light sweeps
    "sparkle": 0.0,  # spark bursts + ring shine
    "glitch": 0.0,  # Twitch RGB split
    "riser": 0.0,  # collapse into the dot
    "impact": 0.0,  # circle reveal hit
    "atmos": 0.0,  # quiet air/sub bed
    "reverb": 0.0,  # send level
}

tl = json.load(open("scripts/timeline.json"))
FPS = tl["fps"]
N = int(round(tl["durationInFrames"] / FPS * SR))
dry = np.zeros((N, 2))
wet = np.zeros((N, 2))  # reverb send


def db(x):
    return 10 ** (x / 20)


def t_of(frame):
    return frame / FPS


def env_exp(n, decay_s, attack_s=0.001):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack_s, 1e-5), 0, 1)
    return a * np.exp(-t / decay_s)


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def hp(x, f, order=2):
    return sosfilt(butter(order, f, "highpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def place(sig, time_s, layer, pan=0.0, send=0.25):
    """Mix a mono (or stereo) signal at time_s with equal-power pan and reverb send."""
    if sig.ndim == 1:
        ang = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(ang), sig * np.sin(ang)], 1)
    g = db(GAIN[layer])
    i0 = int(round(time_s * SR))
    if i0 >= N:
        return
    if i0 < 0:
        sig = sig[-i0:]
        i0 = 0
    sig = sig[: N - i0] * g
    dry[i0 : i0 + len(sig)] += sig
    wet[i0 : i0 + len(sig)] += sig * send


def sine(freq, n, phase=0.0):
    """freq: scalar or per-sample array."""
    f = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    return np.sin(phase + 2 * np.pi * np.cumsum(f) / SR)


def noise(n):
    return RNG.standard_normal(n)


def moving_band_noise(dur, f0, f1, width=0.5, curve=1.0):
    """Noise through a bandpass whose center glides f0 -> f1 (STFT overlap-add)."""
    n = int(dur * SR)
    win = 1024
    hop = win // 4
    w = np.hanning(win)
    src = noise(n + win)
    out = np.zeros(n + win)
    freqs = np.fft.rfftfreq(win, 1 / SR)
    frames = max(1, (n) // hop)
    for k in range(frames):
        p = (k / frames) ** curve
        fc = f0 * (f1 / f0) ** p
        band = np.exp(-0.5 * (np.log(np.maximum(freqs, 1) / fc) / width) ** 2)
        seg = np.fft.rfft(src[k * hop : k * hop + win] * w)
        out[k * hop : k * hop + win] += np.fft.irfft(seg * band) * w
    out = out[:n]
    return out / (np.abs(out).max() + 1e-9)


# ---------------------------------------------------------------- sound designs


def tick(pitch=2600.0):
    """Short glassy UI click like the reference word ticks."""
    n = int(0.06 * SR)
    click = bp(noise(n), 2500, 9000) * env_exp(n, 0.0025)
    tone = sine(pitch, n) * env_exp(n, 0.018, 0.0006)
    body = sine(pitch / 4, n) * env_exp(n, 0.012, 0.0008)
    return 0.55 * click / (np.abs(click).max() + 1e-9) + 0.35 * tone + 0.18 * body


def bell(f0, dur=0.9):
    """Bright bell for the highlighted word (inharmonic partials)."""
    n = int(dur * SR)
    out = np.zeros(n)
    for ratio, amp, dec in [(1, 1.0, 0.35), (2.76, 0.45, 0.18), (5.4, 0.25, 0.09), (8.93, 0.12, 0.05)]:
        out += amp * sine(f0 * ratio, n, RNG.uniform(0, 6.28)) * env_exp(n, dec, 0.002)
    out *= 0.32
    tk = tick(f0 * 2)
    out[: len(tk)] += 0.4 * tk
    return out


def pop(f_start=170.0, f_end=640.0, dur=0.12):
    """Bubbly 'bloop' pop: fast upward pitch sweep + click."""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f_end + (f_start - f_end) * np.exp(-t / 0.012)
    body = sine(f, n) * env_exp(n, 0.035, 0.0015)
    c = tick(3200)
    body[: len(c)] += 0.35 * c[: min(len(c), n)]
    return body


def thump(f0=62.0, dur=0.35):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 38 + (f0 - 38) * np.exp(-t / 0.05)
    return sine(f, n) * env_exp(n, 0.11, 0.003)


def whoosh(dur, f0, f1, width=0.55, peak=0.6, curve=1.0):
    n = int(dur * SR)
    x = moving_band_noise(dur, f0, f1, width, curve)
    t = np.linspace(0, 1, n)
    # asymmetric swell: rises to `peak`, falls after
    e = np.where(t < peak, (t / peak) ** 2, ((1 - t) / (1 - peak)) ** 1.6)
    return x * e


def sparkles(dur, count, lo=3500, hi=10000, decay_rate=3.0):
    """Granular shimmer: tiny high sine grains, density decaying; returns stereo."""
    n = int(dur * SR)
    out = np.zeros((n, 2))
    for _ in range(count):
        st = RNG.exponential(dur / decay_rate)
        if st >= dur - 0.03:
            continue
        i0 = int(st * SR)
        gn = int(0.03 * SR)
        f = RNG.uniform(lo, hi)
        g = sine(f, gn, RNG.uniform(0, 6.28)) * env_exp(gn, RNG.uniform(0.004, 0.012), 0.0005)
        a = RNG.uniform(0.25, 1.0) * np.exp(-st * 2.5)
        pan = RNG.uniform(-0.9, 0.9)
        ang = (pan + 1) * np.pi / 4
        seg = slice(i0, min(n, i0 + gn))
        L = seg.stop - seg.start
        out[seg, 0] += g[:L] * a * np.cos(ang)
        out[seg, 1] += g[:L] * a * np.sin(ang)
    return out


def shine_chord(freqs, dur=1.1):
    """Airy ring 'shine' with soft attack."""
    n = int(dur * SR)
    out = np.zeros(n)
    for i, f in enumerate(freqs):
        vib = 1 + 0.002 * np.sin(2 * np.pi * (4 + i) * np.arange(n) / SR)
        out += sine(f * vib, n, RNG.uniform(0, 6.28)) * env_exp(n, 0.28, 0.02) / len(freqs)
    return out


def riser(dur):
    """Suck-in riser: rising band noise + rising tone, crescendo to the end."""
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    nz = moving_band_noise(dur, 500, 7000, 0.5, 1.6)
    tone = sine(220 * (8 ** (t**1.7)), n) * 0.35
    return (nz * 0.8 + tone) * (t**2.2)


def impact(dur=1.3):
    n = int(dur * SR)
    t = np.arange(n) / SR
    sub = sine(34 + 40 * np.exp(-t / 0.07), n) * env_exp(n, 0.2, 0.002)
    crack = lp(noise(n), 3500) * env_exp(n, 0.05, 0.0008)
    air = hp(noise(n), 4000) * env_exp(n, 0.25, 0.004) * 0.25
    x = sub * 0.95 + crack / (np.abs(crack).max() + 1e-9) * 0.45 + air / (np.abs(air).max() + 1e-9) * 0.2
    return np.tanh(x * 1.4) / np.tanh(1.4)


def glitch(dur):
    """Digital stutter: chopped square buzz + bit-crushed noise, alternating pan; stereo."""
    n = int(dur * SR)
    out = np.zeros((n, 2))
    chunk = int(0.016 * SR)
    for k in range(0, n, chunk):
        L = min(chunk, n - k)
        f = RNG.choice([180, 360, 720, 1440, 2880]) * RNG.uniform(0.95, 1.05)
        sq = np.sign(sine(f, L))
        nz = np.round(noise(L) * 3) / 3
        x = (sq * 0.5 + nz * 0.35) * RNG.uniform(0.4, 1.0)
        x *= np.hanning(L) ** 0.2 if L > 4 else 1
        if RNG.random() < 0.25:
            x *= 0  # dropouts
        side = (k // chunk) % 2
        out[k : k + L, side] += x
        out[k : k + L, 1 - side] += x * 0.4
    return out * 0.6


def blip(f=2200, dur=0.05):
    n = int(dur * SR)
    return sine(f, n) * env_exp(n, 0.012, 0.0008)


def reverb_ir(dur=1.1, decay=0.16):
    n = int(dur * SR)
    t = np.arange(n) / SR
    ir = np.stack([noise(n), noise(n)], 1) * np.exp(-t / decay)[:, None]
    ir = np.stack([lp(ir[:, c], 7000) for c in range(2)], 1)
    ir[: int(0.012 * SR)] *= np.linspace(0, 1, int(0.012 * SR))[:, None]  # pre-delay-ish
    return ir / np.sqrt((ir**2).sum(0))


# ---------------------------------------------------------------- arrange

YT, TW, TR = tl["youtube"], tl["twitch"], tl["transition"]
PITCH = {"youtube": [2350, 2640, 2960, 3520], "twitch": [2490, 2790, 3140, 3730]}
KEY_BELL = {"youtube": 1318.5, "twitch": 1568.0}  # E6 / G6
SHINE = {"youtube": [1046.5, 1568.0, 2093.0, 2637.0], "twitch": [1174.7, 1760.0, 2349.3, 2960.0]}

for S in (YT, TW):
    L = S["logoIn"]
    # logo: whoosh in -> pop + thump on the spring overshoot
    place(whoosh(0.22, 900, 5000, peak=0.85) * 0.35, t_of(L) - 0.12, "whoosh", send=0.3)
    place(pop(160, 700, 0.14) * 0.9, t_of(L + 4), "pop", send=0.3)
    place(thump(70, 0.4) * 0.38, t_of(L + 4), "pop", send=0.05)
    place(whoosh(t_of(28), 5000, 12000, 0.4, 0.5) * 0.12, t_of(S["logoSweep"]), "sheen", pan=-0.3, send=0.4)

    # caption: one tick per word, the key word gets a bell
    for i, w in enumerate(S["captionWords"]):
        p = PITCH[S["id"]][i % 4]
        place(tick(p) * 0.85, t_of(w["frame"] + 2), "tick", pan=(-0.25 + 0.17 * i), send=0.2)
        if w["key"]:
            place(bell(KEY_BELL[S["id"]]) * 0.5, t_of(w["frame"] + 3), "key", pan=0.15, send=0.55)

    # morph: logo shrinks (swish) -> disc grows (bloop) -> ring shine + spark burst
    M = S["morph"]
    place(whoosh(0.3, 3000, 600, 0.5, 0.35) * 0.4, t_of(M) - 0.03, "whoosh", send=0.3)
    place(pop(120, 520, 0.18) * 0.75, t_of(M + 4), "pop", send=0.3)
    place(thump(55, 0.45) * 0.3, t_of(M + 6), "pop", send=0.05)
    place(shine_chord(SHINE[S["id"]]) * 0.33, t_of(M + 10), "sparkle", send=0.7)
    place(sparkles(0.8, 70) * 0.28, t_of(M + 10), "sparkle", send=0.5)

    # nick
    for i, w in enumerate(S["nickWords"]):
        place(tick(PITCH[S["id"]][3 - i] * 0.85) * 0.85, t_of(w["frame"] + 2), "tick", pan=0.1 * (i * 2 - 1), send=0.25)
        place(blip(PITCH[S["id"]][3 - i] * 0.5, 0.12) * 0.12, t_of(w["frame"] + 2), "tick", send=0.4)

    # light sweeps over the avatar
    for s in S["sweeps"]:
        place(whoosh(t_of(30), 4000, 11000, 0.45, 0.5) * 0.13, t_of(s), "sheen", pan=0.25, send=0.5)
        place(sparkles(0.5, 18, 6000, 12000) * 0.12, t_of(s + 8), "sheen", send=0.5)

# ---- transition
place(whoosh(0.28, 1500, 7000, 0.5, 0.4, 0.8) * 0.35, t_of(YT["textExit"]), "whoosh", send=0.35)
for i in range(4):  # quick reversed tick cascade as words blur away
    place(tick(3600 - i * 280) * 0.18, t_of(YT["textExit"] + i * 1.5 + 1), "tick", pan=0.2 - 0.13 * i, send=0.3)
C = YT["collapse"]
rise_dur = t_of(TR["dotStart"] - C + 5)
place(riser(rise_dur) * 0.55, t_of(TR["dotStart"]) - rise_dur, "riser", send=0.25)
place(blip(1760, 0.08) * 0.35, t_of(TR["dotStart"]), "pop", send=0.4)
e0, e1 = TR["expand"]
place(whoosh(t_of(e1 - e0) + 0.25, 300, 4000, 0.7, 0.55) * 0.55, t_of(e0) - 0.04, "whoosh", send=0.4)
place(impact() * 0.95, t_of(TR["flashPeak"] - 1), "impact", send=0.45)
place(sparkles(0.9, 60, 4000, 12000) * 0.22, t_of(TR["flashPeak"]), "sparkle", send=0.6)

# ---- twitch extras: RGB-split glitch and the eye blink
place(glitch(t_of(5)) * 0.42, t_of(TW["logoIn"] + 3), "glitch", send=0.1)
place(blip(2350, 0.04) * 0.3, t_of(TW["logoIn"] + 10), "tick", pan=-0.1, send=0.3)
place(blip(3140, 0.05) * 0.3, t_of(TW["logoIn"] + 14), "tick", pan=0.1, send=0.3)

# ---- atmos: quiet air + sub bed, warm then cool, swelling into the final frame
t = np.arange(N) / SR
air = hp(lp(noise(N), 6000), 1500)
air /= np.abs(air).max()
sw = t_of(TR["auroraSwitch"])
bed_env = np.clip(t / 0.35, 0, 1) * (0.55 + 0.25 * np.clip((t - sw) / 1.2, 0, 1))
bed_env *= 1 - 0.7 * np.exp(-(((t - t_of(TR["flashPeak"])) / 0.05) ** 2))  # duck at the hit
sub = sine(np.where(t < sw, 55.0, 61.7), N) * 0.5 + sine(np.where(t < sw, 82.4, 92.5), N) * 0.25
bed = air * 0.04 + lp(sub, 200) * 0.035
place(np.stack([bed * bed_env, np.roll(bed, 960) * bed_env], 1), 0, "atmos", send=0.0)

# ---------------------------------------------------------------- master
wet = hp(wet.T, 450).T  # keep lows out of the reverb so pops/hits stay tight
ir = reverb_ir()
rev = np.stack([fftconvolve(wet[:, c], ir[:, c])[:N] for c in range(2)], 1)
mix = dry + rev * db(GAIN["reverb"]) * 0.6
mix = hp(mix.T, 25).T  # remove DC / sub rumble
# end: short fade so the last frame stays clean
fade = int(0.06 * SR)
mix[-fade:] *= np.linspace(1, 0, fade)[:, None] ** 2
# gentle bus glue + peak normalize to -1 dBFS (loudness is checked afterwards with ffmpeg)
mix = np.tanh(mix * 1.6) / 1.6
mix *= db(-1.0) / (np.abs(mix).max() + 1e-9)

import os

os.makedirs("public/sfx", exist_ok=True)
sf.write("public/sfx/arut_sfx.wav", mix.astype(np.float32), SR, subtype="PCM_24")
print("public/sfx/arut_sfx.wav", f"{len(mix) / SR:.3f}s")
