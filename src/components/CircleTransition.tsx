import React from 'react';
import {AbsoluteFill, interpolateColors, useCurrentFrame} from 'remotion';
import {cameraFor} from '../camera';
import {COLORS, HEIGHT, LAYOUT, SCENES, TRANSITION, WIDTH} from '../config';
import {easeInOut, lerp, progress, pulse} from '../easing';

/**
 * The collapsed avatar dot recolors red -> purple and expands into a full-screen
 * fill (the reference's expanding plate), flashes, then dissolves into scene 2.
 */
export const CircleTransition: React.FC = () => {
  const frame = useCurrentFrame();
  const end = TRANSITION.fadeOut[1];
  if (frame < TRANSITION.dotStart || frame > end) return null;

  const cam = cameraFor(TRANSITION.dotStart, SCENES.youtube);
  const startD = LAYOUT.dotSize * cam.hero;
  const cx = LAYOUT.centerX;
  const cy = HEIGHT / 2 + (LAYOUT.avatarY - HEIGHT / 2) * cam.hero;
  const cover = 2 * Math.hypot(Math.max(cx, WIDTH - cx), Math.max(cy, HEIGHT - cy)) * 1.05;

  const e = progress(frame, TRANSITION.expand[0], TRANSITION.expand[1], easeInOut);
  // tiny anticipation squeeze before the expansion
  const squeeze = 1 - 0.18 * pulse(frame, TRANSITION.dotStart, TRANSITION.expand[0], TRANSITION.expand[0] + 2);
  const d = lerp(startD, cover, e) * squeeze;
  const color = interpolateColors(
    frame,
    [TRANSITION.recolor[0], TRANSITION.recolor[1]],
    [COLORS.youtube, COLORS.twitch],
  );
  const fade = 1 - progress(frame, TRANSITION.fadeOut[0], TRANSITION.fadeOut[1], easeInOut);
  const flash = pulse(frame, TRANSITION.flashPeak - 3, TRANSITION.flashPeak, TRANSITION.flashPeak + 6);
  const glow = 1 - e;

  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <div
        style={{
          position: 'absolute',
          left: cx - d / 2,
          top: cy - d / 2,
          width: d,
          height: d,
          borderRadius: '50%',
          opacity: fade,
          background: color,
          boxShadow: `0 0 ${40 + glow * 60}px ${10 + glow * 30}px ${color}`,
        }}
      />
      <AbsoluteFill style={{background: COLORS.flash, opacity: flash * TRANSITION.flashOpacity}} />
    </AbsoluteFill>
  );
};
