// Single source of truth for timing, colors and layout.
// All times are in seconds and converted to frames with f().

export const FPS = 60;
export const WIDTH = 1080;
export const HEIGHT = 1920;
export const DURATION_IN_FRAMES = 252; // 4.2 s

export const f = (seconds: number) => Math.round(seconds * FPS);

export const COLORS = {
  bg: '#07070A',
  text: '#FFFFFF',
  youtube: '#FF0033',
  twitch: '#9146FF',
  flash: '#FFFFFF',
};

export const LAYOUT = {
  centerX: WIDTH / 2,
  captionY: 470, // vertical center of the 2-line caption (top third)
  captionSize: 108,
  captionLineHeight: 1.04,
  captionTracking: '-0.035em',
  captionWeight: 700,
  avatarSize: 520,
  avatarY: 980, // avatar center
  nickY: 1365, // nick vertical center
  nickSize: 100,
  nickTracking: '-0.04em',
  nickWeight: 700,
  logoSize: 330, // logo width
  ringGap: 16, // space between avatar and ring
  ringWidth: 5,
  dotSize: 46, // avatar collapses to this dot before the circle reveal
};

export const MOTION = {
  // "Expo out" from the reference and the mandatory soft in-out curve
  easeOut: [0.22, 1, 0.36, 1] as const,
  easeInOut: [0.65, 0, 0.35, 1] as const,
  spring: {damping: 14, stiffness: 150, mass: 1},
  softSpring: {damping: 17, stiffness: 120, mass: 1},
  wordStagger: 3, // frames between words (50 ms)
  wordDuration: 22,
  wordBlur: 14,
  wordRise: 24,
  exitStagger: 1.5,
  exitDuration: 10,
  exitBlur: 16,
  exitRise: 42,
  motionBlur: {shutterAngle: 160, samples: 6},
  pushIn: 0.08, // camera scale gain during holds
};

export type PlatformId = 'youtube' | 'twitch';

export type SceneConfig = {
  id: PlatformId;
  brand: string;
  // caption is laid out by lines, highlight = index of the colored word (global)
  captionLines: string[][];
  highlight: number;
  nick: string[];
  avatar: string;
  aurora: string[];
  ring: {colors: string[]; degPerFrame: number};
  sparkColors: string[];
  t: {
    logoIn: number;
    captionIn: number;
    morph: number;
    nickIn: number;
    holdStart: number;
    holdEnd: number;
    sweeps: number[]; // frames where light sweeps over the avatar start
    logoSweep: number;
    textExit: number | null;
    collapse: number | null; // avatar collapses into a dot
    visibleFrom: number;
    visibleTo: number;
  };
};

export const SCENES: Record<PlatformId, SceneConfig> = {
  youtube: {
    id: 'youtube',
    brand: COLORS.youtube,
    captionLines: [['Смотри', 'стрим'], ['на', 'YouTube']],
    highlight: 3,
    nick: ['Arut', 'Academy'],
    avatar: 'avatar_youtube.png',
    aurora: ['#FF0033', '#FF4D7A', '#FF2D55', '#B3123A', '#FF7A59'],
    ring: {colors: ['#FF0033', '#FFFFFF', '#FF5C7A', '#FFFFFF', '#FF0033'], degPerFrame: 0.6},
    sparkColors: ['#FFFFFF', '#FF5C7A', '#FF0033', '#FFC2CC'],
    t: {
      logoIn: f(0),
      captionIn: f(0.2),
      morph: f(0.6),
      nickIn: f(1.0),
      holdStart: f(1.45),
      holdEnd: f(2.4),
      sweeps: [f(0.95), f(1.75)],
      logoSweep: f(0.1),
      textExit: f(2.4),
      collapse: f(2.45),
      visibleFrom: 0,
      visibleTo: f(2.6),
    },
  },
  twitch: {
    id: 'twitch',
    brand: COLORS.twitch,
    captionLines: [['Смотри', 'стрим'], ['на', 'Twitch']],
    highlight: 3,
    nick: ['@arutmain'],
    avatar: 'avatar_twitch.png',
    aurora: ['#9146FF', '#5B5CFF', '#C04BFF', '#3B2BBF', '#FF5FD2'],
    ring: {colors: ['#9146FF', '#FF5FD2', '#6A5CFF', '#E0B8FF', '#9146FF'], degPerFrame: 2.2},
    sparkColors: ['#FFFFFF', '#C99BFF', '#9146FF', '#FF7FE0'],
    t: {
      logoIn: f(2.7),
      captionIn: f(2.8),
      morph: f(2.95),
      nickIn: f(3.25),
      holdStart: f(3.35),
      holdEnd: DURATION_IN_FRAMES,
      sweeps: [f(3.7)],
      logoSweep: f(2.75),
      textExit: null,
      collapse: null,
      visibleFrom: f(2.62),
      visibleTo: DURATION_IN_FRAMES,
    },
  },
};

// Transition between the scenes (collapse -> dot -> circle reveal)
const COLLAPSE = f(2.45);
export const TRANSITION = {
  collapseDuration: 7, // avatar -> dot
  dotStart: COLLAPSE + 7, // dot is handed over to CircleTransition
  recolor: [COLLAPSE + 5, COLLAPSE + 11] as const, // red -> purple
  expand: [COLLAPSE + 8, COLLAPSE + 15] as const, // dot -> full screen
  flashPeak: COLLAPSE + 13,
  flashOpacity: 0.15,
  fadeOut: [COLLAPSE + 14, COLLAPSE + 23] as const, // fill dissolves into the dark bg
  auroraSwitch: COLLAPSE + 12,
};

// Frames where the hero layer gets camera motion blur (fast moves only)
export const MOTION_BLUR_WINDOWS: [number, number][] = [
  [0, 16],
  [f(0.6), f(0.92)],
  [f(2.45), f(2.62)],
  [f(2.7), f(2.95)],
  [f(2.95), f(3.25)],
];
