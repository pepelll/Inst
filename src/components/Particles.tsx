import React from 'react';
import {AbsoluteFill, random, useCurrentFrame} from 'remotion';
import {HEIGHT, WIDTH} from '../config';
import {easeOut} from '../easing';

/** Fine glowing dust drifting slowly upward across the whole frame. */
export const Dust: React.FC<{colors: string[]; count?: number; opacity?: number; seed: string}> = ({
  colors,
  count = 70,
  opacity = 1,
  seed,
}) => {
  const frame = useCurrentFrame();
  if (opacity <= 0.001) return null;
  return (
    <AbsoluteFill style={{opacity}}>
      {new Array(count).fill(0).map((_, i) => {
        const r = (k: string) => random(`${seed}-dust-${i}-${k}`);
        const size = 1.5 + r('s') ** 2 * 4.5;
        const depth = 0.3 + r('d') * 0.7;
        const x = (r('x') * WIDTH + Math.sin(frame * 0.02 * depth + r('p') * 6.28) * 30 * depth) % WIDTH;
        const y = ((r('y') * HEIGHT - frame * 0.9 * depth) % HEIGHT + HEIGHT) % HEIGHT;
        const twinkle = 0.35 + 0.65 * (0.5 + 0.5 * Math.sin(frame * (0.05 + r('t') * 0.08) + r('o') * 6.28));
        const color = colors[i % colors.length];
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: x,
              top: y,
              width: size,
              height: size,
              borderRadius: '50%',
              background: '#fff',
              opacity: twinkle * depth * 0.85,
              boxShadow: `0 0 ${size * 3}px ${size}px ${color}88`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};

/** Short radial burst of sparks around a point (avatar appearance). */
export const SparkBurst: React.FC<{
  start: number;
  x: number;
  y: number;
  innerRadius: number;
  colors: string[];
  count?: number;
  seed: string;
}> = ({start, x, y, innerRadius, colors, count = 42, seed}) => {
  const frame = useCurrentFrame();
  const local = frame - start;
  if (local < 0 || local > 60) return null;
  return (
    <AbsoluteFill style={{mixBlendMode: 'screen'}}>
      {new Array(count).fill(0).map((_, i) => {
        const r = (k: string) => random(`${seed}-spark-${i}-${k}`);
        const life = 26 + r('l') * 30;
        const delay = r('dl') * 5;
        const t = (local - delay) / life;
        if (t <= 0 || t >= 1) return null;
        const angle = (i / count) * Math.PI * 2 + r('a') * 0.35;
        const dist = innerRadius * 0.9 + easeOut(t) * (90 + r('d') * 260);
        const len = (1 - t) * (14 + r('len') * 34);
        const thick = 2 + r('th') * 2.5;
        const color = colors[i % colors.length];
        const px = x + Math.cos(angle) * dist;
        const py = y + Math.sin(angle) * dist;
        return (
          <div
            key={i}
            style={{
              position: 'absolute',
              left: px - len / 2,
              top: py - thick / 2,
              width: Math.max(thick, len),
              height: thick,
              borderRadius: thick,
              background: `linear-gradient(90deg, ${color}00, #fff)`,
              transform: `rotate(${(angle * 180) / Math.PI}deg)`,
              opacity: (1 - t) ** 1.4,
              boxShadow: `0 0 10px 2px ${color}AA`,
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
