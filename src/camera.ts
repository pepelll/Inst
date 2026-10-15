import {MOTION, SceneConfig} from './config';
import {easeInOut, easeOut, progress} from './easing';

/**
 * Slow push-in with parallax: the hero (logo/avatar) moves most,
 * text a bit less, background the least.
 */
export const cameraFor = (frame: number, scene: SceneConfig) => {
  const {holdStart, holdEnd} = scene.t;
  // The final hold eases out so the last frames settle into a still image
  const p = scene.t.collapse === null
    ? progress(frame, holdStart, holdEnd, easeOut)
    : progress(frame, holdStart, holdEnd + 12, easeInOut);
  const k = MOTION.pushIn;
  return {
    p,
    hero: 1 + k * p * 1.15,
    text: 1 + k * p * 0.8,
    textY: -12 * p,
    bg: 1 + k * p * 0.35,
  };
};
