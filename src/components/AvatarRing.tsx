import React from 'react';

type Props = {
  size: number; // outer diameter
  width: number;
  colors: string[];
  rotation: number;
  glow: number; // 0..1+
};

/** Thin conic-gradient ring with a blurred bloom copy. */
export const AvatarRing: React.FC<Props> = ({size, width, colors, rotation, glow}) => {
  const ring = (extra: React.CSSProperties = {}) => (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        borderRadius: '50%',
        background: `conic-gradient(from ${rotation}deg, ${colors.join(', ')})`,
        WebkitMaskImage: `radial-gradient(circle closest-side, transparent calc(100% - ${width + 0.8}px), #000 calc(100% - ${width}px), #000 calc(100% - 0.8px), transparent 100%)`,
        maskImage: `radial-gradient(circle closest-side, transparent calc(100% - ${width + 0.8}px), #000 calc(100% - ${width}px), #000 calc(100% - 0.8px), transparent 100%)`,
        ...extra,
      }}
    />
  );
  return (
    <div style={{position: 'absolute', width: size, height: size, left: -size / 2, top: -size / 2}}>
      {ring({filter: `blur(${10 + glow * 10}px)`, opacity: Math.min(1, 0.35 + glow * 0.65), transform: 'scale(1.01)', mixBlendMode: 'screen'})}
      {ring({filter: `blur(${3 + glow * 3}px)`, opacity: Math.min(1, 0.4 + glow * 0.5), mixBlendMode: 'screen'})}
      {ring()}
    </div>
  );
};
