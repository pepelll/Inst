import {loadFont} from '@remotion/fonts';
import {staticFile} from 'remotion';
import manifest from './fonts.json';

// Inter Tight (Google Fonts, variable) self-hosted from public/fonts,
// fetched by scripts/fetch-fonts.mjs via @remotion/google-fonts metadata.
export const fontFamily = 'Inter Tight';

for (const {file, unicodeRange} of manifest) {
  loadFont({family: fontFamily, url: staticFile(file), weight: '100 900', unicodeRange, format: 'woff2'});
}
