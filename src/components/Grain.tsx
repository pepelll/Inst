import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {HEIGHT, WIDTH} from '../config';

/** Animated film grain (~2-3 %) and a soft vignette. */
export const Grain: React.FC<{opacity?: number}> = ({opacity = 0.03}) => {
  const frame = useCurrentFrame();
  const w = WIDTH / 2;
  const h = HEIGHT / 2;
  return (
    <AbsoluteFill style={{opacity, pointerEvents: 'none'}}>
      <svg width={WIDTH} height={HEIGHT} viewBox={`0 0 ${w} ${h}`} preserveAspectRatio="none">
        <filter id={`grain-${frame}`} x="0" y="0">
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={frame % 97} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width={w} height={h} filter={`url(#grain-${frame})`} />
      </svg>
    </AbsoluteFill>
  );
};

export const Vignette: React.FC<{strength?: number}> = ({strength = 0.6}) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 78% 62% at 50% 50%, rgba(0,0,0,0) 55%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);
