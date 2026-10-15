import React from 'react';
import {siTwitch, siYoutube} from 'simple-icons';
import {COLORS} from '../config';

// simple-icons paths, split so parts can be colored / animated separately
const YT_PLAY = 'M9.545 15.568V8.432L15.818 12l-6.273 3.568z';
const TW_EYES = ['M11.571 4.714h1.715v5.143H11.57z', 'M16.286 4.714H18v5.143h-1.714z'];
const TW_BODY = siTwitch.path.slice(siTwitch.path.indexOf('M6 0'));
const TW_INNER = 'M20.571 11.143L17.143 14.571H13.714L10.714 17.571V14.571H6.857V1.714H20.571Z';

export const LOGO_ASPECT: Record<'youtube' | 'twitch', number> = {
  youtube: 24 / 17.05, // visible glyph is wider than tall
  twitch: 1,
};

const svgMask = (paths: string[], viewBox: string) =>
  `url("data:image/svg+xml;utf8,${encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' viewBox='${viewBox}' preserveAspectRatio='none'>${paths
      .map((d) => `<path fill='white' d='${d}'/>`)
      .join('')}</svg>`,
  )}")`;

export const YT_VIEWBOX = '0 3.475 24 17.05';
export const TW_VIEWBOX = '0 0 24 24';
export const YT_MASK = svgMask([siYoutube.path, YT_PLAY], YT_VIEWBOX);
export const TW_MASK = svgMask([TW_BODY, TW_INNER], TW_VIEWBOX);

export const YouTubeLogo: React.FC<{width: number; color?: string}> = ({width, color = COLORS.youtube}) => (
  <svg width={width} height={width / LOGO_ASPECT.youtube} viewBox={YT_VIEWBOX} style={{display: 'block'}}>
    <path d={YT_PLAY} fill="#fff" />
    <path d={siYoutube.path} fill={color} />
  </svg>
);

export const TwitchLogo: React.FC<{width: number; eyeScaleY?: number; color?: string; inner?: string}> = ({
  width,
  eyeScaleY = 1,
  color = COLORS.twitch,
  inner = '#fff',
}) => (
  <svg width={width} height={width} viewBox={TW_VIEWBOX} style={{display: 'block'}}>
    <path d={TW_INNER} fill={inner} />
    <path d={TW_BODY} fill={color} />
    <g transform={`translate(0 7.286) scale(1 ${eyeScaleY}) translate(0 -7.286)`}>
      {TW_EYES.map((d) => (
        <path key={d} d={d} fill={color} />
      ))}
    </g>
  </svg>
);
