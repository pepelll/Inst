// Export SFX event times (in frames) straight from src/config.ts so audio stays in sync with the picture.
// Run: node --experimental-strip-types scripts/export-timeline.mjs
import {writeFileSync} from 'node:fs';
const {FPS, DURATION_IN_FRAMES, MOTION, SCENES, TRANSITION} = await import('../src/config.ts');

const scene = (s) => {
  const words = s.captionLines.flat();
  return {
    id: s.id,
    logoIn: s.t.logoIn,
    logoSweep: s.t.logoSweep,
    captionWords: words.map((w, i) => ({frame: s.t.captionIn + i * MOTION.wordStagger, key: i === s.highlight})),
    morph: s.t.morph,
    nickWords: s.nick.map((w, i) => ({frame: s.t.nickIn + i * 5})),
    sweeps: s.t.sweeps,
    textExit: s.t.textExit,
    collapse: s.t.collapse,
  };
};

const timeline = {
  fps: FPS,
  durationInFrames: DURATION_IN_FRAMES,
  youtube: scene(SCENES.youtube),
  twitch: scene(SCENES.twitch),
  transition: TRANSITION,
};
writeFileSync('scripts/timeline.json', JSON.stringify(timeline, null, 2));
console.log(JSON.stringify(timeline));
