import React from 'react';
import {useCurrentFrame} from 'remotion';
import {easeInOut, progress} from '../easing';

type Props = {
  start: number;
  duration?: number;
  angle?: number;
  intensity?: number;
  maskImage?: string; // clip the sweep to a shape (e.g. a logo); otherwise parent clips
};

/** Diagonal highlight band that travels across its parent. */
export const LightSweep: React.FC<Props> = ({start, duration = 26, angle = 20, intensity = 0.6, maskImage}) => {
  const frame = useCurrentFrame();
  if (frame < start || frame > start + duration) return null;
  const p = progress(frame, start, start + duration, easeInOut);
  const x = -130 + p * 260; // % of the parent width
  const fade = Math.sin(p * Math.PI);
  const mask = maskImage
    ? {
        WebkitMaskImage: maskImage,
        maskImage,
        WebkitMaskSize: '100% 100%',
        maskSize: '100% 100%',
      }
    : {};
  return (
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none', ...mask}}>
      <div
        style={{
          position: 'absolute',
          top: '-50%',
          bottom: '-50%',
          left: `${x}%`,
          width: '55%',
          transform: `rotate(${angle}deg)`,
          background:
            'linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.18) 35%, rgba(255,255,255,0.85) 50%, rgba(255,255,255,0.18) 65%, rgba(255,255,255,0) 100%)',
          mixBlendMode: 'screen',
          opacity: intensity * fade,
        }}
      />
    </div>
  );
};
