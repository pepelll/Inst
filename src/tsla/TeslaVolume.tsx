import React from 'react';
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from 'remotion';
import {fontFamily} from '../fonts';
import {clamp, easeInOut, easeOut, progress, pulse, springAt} from '../easing';
import {Grain, Vignette} from '../components/Grain';
import {BARS, FOCUS_FROM, LAST, PREV, PRICE_CHANGE} from './data';
import {T, TSLA_DURATION} from './timing';

const W = 1080;

const C = {
  bg: '#000000',
  em: '#2CFFB0', // emerald highlight
  emMid: '#14D592',
  emDeep: '#0A7A55',
  text: '#F4FFFA',
};

// ---- layout
const X0 = 96;
const X1 = 984;
const SLOT = (X1 - X0) / BARS.length;
const cx = (i: number) => X0 + SLOT * (i + 0.5);
const CW = 58; // candle / volume bar width
const RX = 18;

const PY0 = 500;
const PY1 = 1080;
const PMIN = 348;
const PMAX = 390;
const py = (p: number) => PY1 - ((p - PMIN) / (PMAX - PMIN)) * (PY1 - PY0);

const VB = 1720; // volume baseline
const VH = 400; // height of the tallest (last) bar
const VMAX = Math.max(...BARS.map((b) => b.v));
const vh = (v: number) => (v / VMAX) * VH;

const N = BARS.length;
const LI = N - 1;
const LX = cx(LI);

const candleSpring = {damping: 16, stiffness: 150, mass: 1};
const barSpring = {damping: 15, stiffness: 120, mass: 1};
const spikeSpring = {damping: 10, stiffness: 70, mass: 1};

const easeIn = Easing.bezier(0.55, 0, 0.9, 0.45);

const glow = (a: number, r = 22) =>
  `drop-shadow(0 0 ${r * 0.35}px rgba(44,255,176,${0.9 * a})) drop-shadow(0 0 ${r}px rgba(44,255,176,${0.45 * a}))`;

const pill = (x: number, y0: number, y1: number, w: number, r = RX) => {
  const h = Math.max(0, y1 - y0);
  return {x: x - w / 2, y: y0, width: w, height: h, rx: Math.min(r, h / 2, w / 2)};
};

// ---- ghost path: previous close -> straight up "to space"
const G0 = {x: cx(LI - 1), y: py(PREV.c)};
const G1 = {x: cx(LI - 1) + 46, y: py(PREV.c) - 70};
const G2 = {x: LX, y: 640};
const G3 = {x: LX, y: -120};
const bez = (t: number) => {
  const u = 1 - t;
  const a = u * u * u, b = 3 * u * u * t, c = 3 * u * t * t, d = t * t * t;
  return {x: a * G0.x + b * G1.x + c * G2.x + d * G3.x, y: a * G0.y + b * G1.y + c * G2.y + d * G3.y};
};
const APEX_T = 0.84;
const ghostPath = (tEnd: number) => {
  const steps = 60;
  let d = '';
  for (let k = 0; k <= steps; k++) {
    const p = bez((k / steps) * tEnd);
    d += `${k === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`;
  }
  return d;
};

const fmtPct = (x: number) => `${x < 0 ? '−' : '+'}${Math.abs(x).toFixed(1).replace('.', ',')}%`;

export const TeslaVolume: React.FC = () => {
  const frame = useCurrentFrame();

  // camera: slow push towards the last days, a small extra nudge on the spike
  const cam =
    1 + 0.045 * progress(frame, 0, TSLA_DURATION, easeInOut) + 0.012 * pulse(frame, T.spike, T.spikePeak + 8, T.ghostApex);

  const bgIn = progress(frame, T.bgIn[0], T.bgIn[1]);
  const dimCtx = interpolate(frame, [T.spike + 30, T.land], [0.55, 0.36], {...clamp, easing: easeInOut});
  const dimFocus = interpolate(frame, [T.land, T.land + 40], [1, 0.62], {...clamp, easing: easeInOut});

  // volume spike
  const spikeK = springAt(frame, T.spike, spikeSpring);
  const spikeFlash = pulse(frame, T.spike + 4, T.spikePeak, T.spikePeak + 70);
  const bloom = bgIn * (0.14 + 0.32 * spikeFlash + 0.1 * progress(frame, T.spike, T.spikePeak + 20));

  // ghost dot
  const upT = progress(frame, T.ghostLaunch, T.ghostApex, easeOut) * APEX_T;
  const apex = bez(APEX_T);
  const landY = py(LAST.c);
  const fallK = interpolate(frame, [T.fallStart, T.land], [0, 1], {...clamp, easing: easeIn});
  const falling = frame >= T.fallStart;
  const dot = falling ? {x: apex.x, y: apex.y + (landY - apex.y) * fallK} : bez(upT);
  const dotOn =
    progress(frame, T.ghostLaunch - 6, T.ghostLaunch + 6) * (1 - progress(frame, T.land, T.land + 14, easeInOut));
  const pathOpacity = 1 - progress(frame, T.ghostApex - 2, T.ghostApex + 22, easeInOut);
  const landFlash = pulse(frame, T.land - 2, T.land + 3, T.land + 40);

  // last candle is traced by the falling dot
  const traceY = frame >= T.land ? Infinity : falling ? dot.y : -Infinity;

  return (
    <AbsoluteFill style={{background: C.bg, fontFamily}}>
      {/* ambient emerald haze */}
      <AbsoluteFill
        style={{
          opacity: bgIn,
          background: `radial-gradient(ellipse 70% 38% at 70% 62%, rgba(20,213,146,0.07), rgba(0,0,0,0) 70%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: bloom,
          background: `radial-gradient(ellipse 46% 26% at ${(LX / W) * 100}% 78%, rgba(44,255,176,0.55), rgba(10,122,85,0.12) 45%, rgba(0,0,0,0) 75%)`,
        }}
      />

      <AbsoluteFill style={{transform: `scale(${cam})`, transformOrigin: `${LX}px 1080px`}}>
        <Header frame={frame} />

        <svg width={W} height={1920} style={{position: 'absolute', inset: 0, overflow: 'visible'}}>
          <defs>
            <linearGradient id="up" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor={C.em} />
              <stop offset="1" stopColor={C.emMid} />
            </linearGradient>
            <linearGradient id="spike" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#B9FFE4" />
              <stop offset="0.18" stopColor={C.em} />
              <stop offset="1" stopColor={C.emDeep} />
            </linearGradient>
            <linearGradient id="sweep" x1="0" y1="1" x2="0" y2="0">
              <stop offset="0" stopColor="#fff" stopOpacity="0" />
              <stop offset="0.5" stopColor="#fff" stopOpacity="0.55" />
              <stop offset="1" stopColor="#fff" stopOpacity="0" />
            </linearGradient>
            <clipPath id="spikeClip">
              <rect {...pill(LX, VB - vh(LAST.v) * spikeK, VB, CW)} />
            </clipPath>
          </defs>

          {/* volume baseline */}
          <line
            x1={X0}
            x2={X0 + (X1 - X0) * progress(frame, T.baseline[0], T.baseline[1], easeInOut)}
            y1={VB + 22}
            y2={VB + 22}
            stroke={C.em}
            strokeOpacity={0.16}
            strokeWidth={2}
            strokeLinecap="round"
          />

          {/* candles (all but the last) */}
          {BARS.slice(0, LI).map((b, i) => {
            const start = T.candlesIn + i * T.candleStagger;
            const k = Math.min(springAt(frame, start, candleSpring), 1.04);
            const op = progress(frame, start, start + 14);
            const blur = (1 - progress(frame, start, start + 20)) * 8;
            const focus = i >= FOCUS_FROM;
            const a = (focus ? dimFocus : dimCtx) * op;
            return (
              <Candle key={b.date} i={i} k={k} opacity={a} blur={blur} glowA={focus ? dimFocus : 0} rise={(1 - op) * 26} />
            );
          })}

          {/* last candle, traced by the dot */}
          <LastCandle traceY={traceY} opacity={dimFocus === 1 ? 1 : 0.4 + 0.6 * dimFocus} landFlash={landFlash} />

          {/* volume bars */}
          {BARS.slice(0, LI).map((b, i) => {
            const start = T.volumesIn + i * T.volumeStagger;
            const k = springAt(frame, start, barSpring);
            const op = progress(frame, start, start + 12);
            const focus = i >= FOCUS_FROM;
            return (
              <rect
                key={b.date}
                {...pill(cx(i), VB - vh(b.v) * k, VB, CW)}
                fill={C.em}
                opacity={op * (focus ? 0.5 * (0.6 + 0.4 * dimFocus) : dimCtx * 0.5)}
              />
            );
          })}

          {/* the spike */}
          {frame >= T.spike ? (
            <g style={{filter: glow(0.7 + 0.6 * spikeFlash, 26 + 30 * spikeFlash)}}>
              <rect {...pill(LX, VB - vh(LAST.v) * spikeK, VB, CW)} fill="url(#spike)" />
            </g>
          ) : null}
          {frame >= T.sweep ? (
            <g clipPath="url(#spikeClip)">
              <rect
                x={LX - CW}
                width={CW * 2}
                height={220}
                y={interpolate(frame, [T.sweep, T.sweep + 34], [VB, VB - vh(LAST.v) - 220], {...clamp, easing: easeInOut})}
                fill="url(#sweep)"
                opacity={0.7}
              />
            </g>
          ) : null}

          {/* ghost trajectory "to space" */}
          {frame >= T.ghostLaunch - 6 && frame < T.land + 20 ? (
            <g opacity={pathOpacity} style={{filter: `blur(${(1 - pathOpacity) * 6}px) ${glow(0.6, 14)}`}}>
              <path
                d={ghostPath(falling ? APEX_T : Math.max(upT, 0.001))}
                fill="none"
                stroke={C.em}
                strokeWidth={4}
                strokeDasharray="0.1 16"
                strokeLinecap="round"
              />
            </g>
          ) : null}
          {dotOn > 0 ? (
            <g opacity={dotOn}>
              <circle cx={dot.x} cy={dot.y} r={34} fill={C.em} opacity={0.16} style={{filter: 'blur(10px)'}} />
              <circle cx={dot.x} cy={dot.y} r={10} fill="#E9FFF6" style={{filter: glow(1, 18)}} />
            </g>
          ) : null}
        </svg>

        {/* chips */}
        <Chip
          frame={frame}
          start={T.spike + 10}
          x={LX - 12}
          y={VB - VH - 40}
          label="объём"
          value={`${Math.round(LAST.v * progress(frame, T.spike, T.spikePeak + 14, easeOut))}M`}
          accent
        />
        <Chip frame={frame} start={T.priceChip} x={LX - 12} y={py(LAST.h) - 46} label="цена" value={fmtPct(PRICE_CHANGE)} />
      </AbsoluteFill>

      <Vignette strength={0.5} />
      <Grain opacity={0.025} />
    </AbsoluteFill>
  );
};

const Candle: React.FC<{i: number; k: number; opacity: number; blur: number; glowA: number; rise: number}> = ({
  i,
  k,
  opacity,
  blur,
  glowA,
  rise,
}) => {
  const b = BARS[i];
  const up = b.c >= b.o;
  const yTop = py(Math.max(b.o, b.c));
  const yBot = py(Math.min(b.o, b.c));
  const mid = (yTop + yBot) / 2;
  const half = Math.max((yBot - yTop) / 2, 6) * k;
  const wMid = (py(b.h) + py(b.l)) / 2;
  const wHalf = ((py(b.l) - py(b.h)) / 2) * k;
  const x = cx(i);
  const filters = [blur > 0.05 ? `blur(${blur}px)` : '', glowA > 0 ? glow(0.55 * glowA, 18) : ''].join(' ').trim();
  return (
    <g opacity={opacity} transform={`translate(0 ${rise})`} style={filters ? {filter: filters} : undefined}>
      <rect {...pill(x, wMid - wHalf, wMid + wHalf, 4, 2)} fill={C.em} opacity={0.75} />
      {up ? (
        <rect {...pill(x, mid - half, mid + half, CW)} fill="url(#up)" />
      ) : (
        <rect
          {...pill(x, mid - half + 1.5, mid + half - 1.5, CW - 3)}
          fill="#000"
          stroke={C.em}
          strokeWidth={3}
        />
      )}
    </g>
  );
};

const LastCandle: React.FC<{traceY: number; opacity: number; landFlash: number}> = ({traceY, opacity, landFlash}) => {
  const b = LAST;
  const yH = py(b.h);
  const yL = py(b.l);
  const yO = py(b.o);
  const yC = py(b.c);
  if (traceY <= yH) return null;
  const wickEnd = Math.min(traceY, yL);
  const bodyEnd = Math.min(traceY, yC);
  return (
    <g opacity={opacity} style={{filter: glow(0.7 + 0.8 * landFlash, 20 + 24 * landFlash)}}>
      <rect {...pill(LX, yH, wickEnd, 4, 2)} fill={C.em} opacity={0.85} />
      {bodyEnd > yO ? (
        <>
          <rect {...pill(LX, yO + 1.5, bodyEnd - 1.5, CW - 3)} fill="#000" />
          <rect {...pill(LX, yO + 1.5, bodyEnd - 1.5, CW - 3)} fill="rgba(44,255,176,0.12)" stroke={C.em} strokeWidth={3} />
        </>
      ) : null}
    </g>
  );
};

const Header: React.FC<{frame: number}> = ({frame}) => {
  const p = progress(frame, T.header, T.header + 30);
  const p2 = progress(frame, T.header + 6, T.header + 36);
  return (
    <div style={{position: 'absolute', left: X0, top: 330}}>
      <div
        style={{
          fontSize: 54,
          fontWeight: 700,
          letterSpacing: '-0.02em',
          color: C.text,
          opacity: p,
          transform: `translateY(${(1 - p) * 18}px)`,
          filter: `blur(${(1 - p) * 10}px)`,
          display: 'flex',
          alignItems: 'center',
          gap: 18,
        }}
      >
        <span
          style={{
            width: 14,
            height: 14,
            borderRadius: 7,
            background: C.em,
            boxShadow: `0 0 14px ${C.em}, 0 0 30px rgba(44,255,176,0.5)`,
          }}
        />
        TSLA
      </div>
      <div
        style={{
          marginTop: 6,
          marginLeft: 32,
          fontSize: 28,
          fontWeight: 500,
          letterSpacing: '0.02em',
          color: C.text,
          opacity: 0.38 * p2,
          filter: `blur(${(1 - p2) * 8}px)`,
        }}
      >
        {BARS[0].date.split(' ')[0]}–{LAST.date}
      </div>
    </div>
  );
};

const Chip: React.FC<{frame: number; start: number; x: number; y: number; label: string; value: string; accent?: boolean}> = ({
  frame,
  start,
  x,
  y,
  label,
  value,
  accent,
}) => {
  const p = progress(frame, start, start + 22);
  const pl = progress(frame, start + 4, start + 26);
  if (frame < start) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: x - 200,
        width: 400,
        top: y,
        transform: 'translateY(-100%)',
        textAlign: 'center',
        color: C.text,
      }}
    >
      <div
        style={{
          fontSize: 24,
          fontWeight: 600,
          letterSpacing: '0.18em',
          textTransform: 'uppercase',
          opacity: 0.46 * pl,
          filter: `blur(${(1 - pl) * 6}px)`,
          marginBottom: 2,
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontSize: 76,
          fontWeight: 700,
          letterSpacing: '-0.035em',
          lineHeight: 1,
          fontVariantNumeric: 'tabular-nums',
          opacity: p,
          transform: `translateY(${(1 - p) * 20}px)`,
          filter: `blur(${(1 - p) * 12}px)`,
          color: accent ? '#DFFFF2' : C.text,
          textShadow: accent ? '0 0 22px rgba(44,255,176,0.75), 0 0 60px rgba(44,255,176,0.35)' : 'none',
        }}
      >
        {value}
      </div>
    </div>
  );
};
