import React from 'react';

type Props = {
  color: string;
  strength: number; // 0..1, ~0.6 is the resting bloom
  radius?: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
};

const hexA = (hex: string, a: number) =>
  `${hex}${Math.round(Math.max(0, Math.min(1, a)) * 255)
    .toString(16)
    .padStart(2, '0')}`;

/**
 * Layered bloom: a blurred, saturated copy of the element screened underneath
 * plus stacked drop-shadows on the element itself.
 */
export const Glow: React.FC<Props> = ({color, strength, radius = 40, children, style}) => {
  const s = Math.max(0, strength);
  return (
    <div style={{position: 'relative', ...style}}>
      {s > 0.01 ? (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            filter: `blur(${radius}px) saturate(1.5)`,
            opacity: Math.min(0.85, s * 0.7),
            mixBlendMode: 'screen',
            transform: 'scale(1.04)',
          }}
        >
          {children}
        </div>
      ) : null}
      <div
        style={{
          position: 'relative',
          filter:
            s > 0.01
              ? `drop-shadow(0 0 ${radius * 0.18}px ${hexA(color, 0.55 * s)}) drop-shadow(0 0 ${radius * 0.6}px ${hexA(
                  color,
                  0.45 * s,
                )})`
              : undefined,
        }}
      >
        {children}
      </div>
    </div>
  );
};

export {hexA};
