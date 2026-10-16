// Export the TSLA insert timing (frames) so scripts/tsla_sfx.py stays in sync with the picture.
import {writeFileSync} from 'node:fs';
const {T, TSLA_FPS, TSLA_DURATION} = await import('../src/tsla/timing.ts');
const {BARS} = await import('../src/tsla/data.ts');
writeFileSync('scripts/tsla_timeline.json', JSON.stringify({fps: TSLA_FPS, durationInFrames: TSLA_DURATION, bars: BARS.length, ...T}, null, 2));
