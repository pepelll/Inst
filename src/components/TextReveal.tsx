import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {MOTION} from '../config';
import {clamp, easeInOut, easeOut} from '../easing';
import {hexA} from './Glow';

type Props = {
  lines: string[][];
  start: number;
  exitAt?: number | null;
  highlight?: number; // global word index
  highlightColor?: string;
  fontFamily: string;
  fontSize: number;
  fontWeight: number;
  tracking: string;
  lineHeight?: number;
  color?: string;
  stagger?: number;
  duration?: number;
};

/**
 * Word-by-word reveal from the reference: every word rises out of a blur
 * (blur 14 -> 0, y +24 -> 0) with a 50 ms stagger; exits with blur + upward drift.
 */
export const TextReveal: React.FC<Props> = ({
  lines,
  start,
  exitAt = null,
  highlight = -1,
  highlightColor = '#fff',
  fontFamily,
  fontSize,
  fontWeight,
  tracking,
  lineHeight = 1.05,
  color = '#fff',
  stagger = MOTION.wordStagger,
  duration = MOTION.wordDuration,
}) => {
  const frame = useCurrentFrame();
  let index = -1;

  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', lineHeight, fontFamily, fontSize}}>
      {lines.map((line, li) => (
        <div key={li} style={{display: 'flex', justifyContent: 'center', gap: '0.26em', whiteSpace: 'nowrap'}}>
          {line.map((word) => {
            index++;
            const s = start + index * stagger;
            const tIn = interpolate(frame, [s, s + duration], [0, 1], {...clamp, easing: easeOut});
            // opacity a touch faster than the move, like the reference
            const oIn = interpolate(frame, [s, s + duration * 0.55], [0, 1], {...clamp, easing: easeOut});
            let blur = (1 - tIn) * MOTION.wordBlur;
            let y = (1 - tIn) * MOTION.wordRise;
            let opacity = oIn;
            if (exitAt !== null) {
              const e = exitAt + index * MOTION.exitStagger;
              const tOut = interpolate(frame, [e, e + MOTION.exitDuration], [0, 1], {...clamp, easing: easeInOut});
              blur += tOut * MOTION.exitBlur;
              y -= tOut * MOTION.exitRise;
              opacity *= 1 - tOut;
            }
            const isKey = index === highlight;
            const glowIn = isKey ? tIn : 0;
            return (
              <span
                key={word + index}
                style={{
                  display: 'inline-block',
                  fontSize,
                  fontWeight,
                  letterSpacing: tracking,
                  color: isKey ? highlightColor : color,
                  opacity,
                  transform: `translateY(${y}px)`,
                  filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
                  textShadow: isKey
                    ? `0 0 ${fontSize * 0.12}px ${hexA(highlightColor, 0.55 * glowIn)}, 0 0 ${fontSize * 0.45}px ${hexA(
                        highlightColor,
                        0.45 * glowIn,
                      )}, 0 0 ${fontSize * 1.1}px ${hexA(highlightColor, 0.3 * glowIn)}`
                    : `0 0 ${fontSize * 0.5}px rgba(255,255,255,${0.1 * tIn})`,
                }}
              >
                {word}
              </span>
            );
          })}
        </div>
      ))}
    </div>
  );
};
