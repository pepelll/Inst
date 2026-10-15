import {Easing, interpolate, spring} from 'remotion';
import {FPS, MOTION} from './config';

export const easeOut = Easing.bezier(...MOTION.easeOut);
export const easeInOut = Easing.bezier(...MOTION.easeInOut);

const clamp = {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'} as const;

/** 0..1 progress between two frames with the given easing. */
export const progress = (frame: number, from: number, to: number, easing = easeOut) =>
  interpolate(frame, [from, to], [0, 1], {...clamp, easing});

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

/** Spring that starts at `from` (may overshoot past 1). */
export const springAt = (frame: number, from: number, config = MOTION.spring) =>
  frame < from ? 0 : spring({frame: frame - from, fps: FPS, config});

/** Smooth 0 -> 1 -> 0 bump, peaking at `peak`. */
export const pulse = (frame: number, start: number, peak: number, end: number) => {
  if (frame <= start || frame >= end) return 0;
  return frame < peak ? easeOut((frame - start) / (peak - start)) : 1 - easeInOut((frame - peak) / (end - peak));
};

export {clamp};
