// Download Inter Tight woff2 files (from @remotion/google-fonts metadata) into public/fonts
import {getInfo} from '@remotion/google-fonts/InterTight';
import {execFileSync} from 'node:child_process';
import {mkdirSync, writeFileSync} from 'node:fs';

const info = getInfo();
const weights = ['700']; // variable font: one file covers 100-900
const subsets = ['latin', 'cyrillic'];
mkdirSync('public/fonts', {recursive: true});
const manifest = [];
for (const w of weights) {
  for (const s of subsets) {
    const url = info.fonts.normal[w][s];
    const file = `fonts/InterTight-${s}.woff2`;
    execFileSync('curl', ['-sSfL', '-o', `public/${file}`, url]);
    manifest.push({weight: w, subset: s, file, unicodeRange: info.unicodeRanges[s]});
  }
}
writeFileSync('src/fonts.json', JSON.stringify(manifest, null, 2));
console.log(manifest.map((m) => m.file).join('\n'));
