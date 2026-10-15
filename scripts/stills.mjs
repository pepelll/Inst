// Bundle once and render control stills: node scripts/stills.mjs [frames...]
import {bundle} from '@remotion/bundler';
import {renderStill, selectComposition} from '@remotion/renderer';
import path from 'node:path';

const frames = process.argv.slice(2).map(Number);
const list = frames.length ? frames : [10, 35, 60, 85, 120, 145, 152, 160, 170, 190, 210, 251];
const browserExecutable = '/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell';
const serveUrl = await bundle({entryPoint: path.resolve('src/index.ts')});
const composition = await selectComposition({serveUrl, id: 'ArutPromo', browserExecutable});
for (const frame of list) {
  const output = path.resolve(`stills/f${String(frame).padStart(3, '0')}.png`);
  const t = Date.now();
  await renderStill({serveUrl, composition, frame, output, browserExecutable, imageFormat: 'png'});
  console.log(frame, `${Date.now() - t}ms`);
}
