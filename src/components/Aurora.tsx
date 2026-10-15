import React from 'react';
import {AbsoluteFill, random, useCurrentFrame} from 'remotion';
import {HEIGHT, WIDTH} from '../config';

type Props = {
  colors: string[];
  intensity: number; // 0..1+
  seed: string;
  blur?: number;
  scale?: number;
};

/** Large drifting radial blobs of light, blurred and screened over the dark background. */
export const Aurora: React.FC<Props> = ({colors, intensity, seed, blur = 160, scale = 1}) => {
  const frame = useCurrentFrame();
  if (intensity <= 0.001) return null;

  // Blobs are biased towards the edges / top & bottom so the center stays readable
  const anchors = [
    [0.15, 0.18],
    [0.9, 0.3],
    [0.2, 0.62],
    [0.85, 0.82],
    [0.5, 1.02],
    [0.55, -0.02],
  ];

  return (
    <AbsoluteFill style={{mixBlendMode: 'screen', opacity: Math.min(1, intensity), transform: `scale(${scale})`}}>
      <AbsoluteFill style={{filter: `blur(${blur}px)`}}>
        {anchors.map(([ax, ay], i) => {
          const r = (k: string) => random(`${seed}-${i}-${k}`);
          const size = (0.55 + r('s') * 0.45) * WIDTH * 1.1;
          const speed = 0.006 + r('v') * 0.008;
          const x = ax * WIDTH + Math.sin(frame * speed + r('p') * 6.28) * 120;
          const y = ay * HEIGHT + Math.cos(frame * speed * 0.8 + r('q') * 6.28) * 160;
          const color = colors[i % colors.length];
          const alpha = (0.55 + r('a') * 0.35) * Math.min(1.25, intensity);
          return (
            <div
              key={i}
              style={{
                position: 'absolute',
                left: x - size / 2,
                top: y - size / 2,
                width: size,
                height: size,
                borderRadius: '50%',
                background: `radial-gradient(circle at 50% 50%, ${color} 0%, ${color}99 30%, transparent 68%)`,
                opacity: Math.min(1, alpha),
              }}
            />
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
