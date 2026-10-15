import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {fontFamily} from './fonts';
import {CameraMotionBlur} from '@remotion/motion-blur';
import {cameraFor} from './camera';
import {COLORS, DURATION_IN_FRAMES, MOTION, SCENES, TRANSITION} from './config';
import {easeOut, progress} from './easing';
import {Aurora} from './components/Aurora';
import {CircleTransition} from './components/CircleTransition';
import {Grain, Vignette} from './components/Grain';
import {Dust} from './components/Particles';
import {PlatformScene} from './scenes/PlatformScene';


export const ArutPromo: React.FC = () => {
  const frame = useCurrentFrame();
  const yt = SCENES.youtube;
  const tw = SCENES.twitch;
  const isScene1 = frame < TRANSITION.auroraSwitch;
  const cam = cameraFor(frame, isScene1 ? yt : tw);

  // background: fades up in 0..0.35 s, warm aurora for YouTube, violet for Twitch
  const bgIn = progress(frame, 0, 21);
  const warm = bgIn * (0.9 + 0.15 * progress(frame, yt.t.holdStart, yt.t.holdEnd));
  const cool =
    progress(frame, TRANSITION.auroraSwitch, tw.t.logoIn + 14, easeOut) * 0.95 +
    0.3 * progress(frame, tw.t.holdStart, DURATION_IN_FRAMES, easeOut);

  return (
    <AbsoluteFill style={{background: COLORS.bg}}>
      <AbsoluteFill style={{transform: `scale(${cam.bg})`}}>
        {isScene1 ? (
          <Aurora colors={yt.aurora} intensity={warm} seed="warm" />
        ) : (
          <Aurora colors={tw.aurora} intensity={cool} seed="cool" />
        )}
        <Dust colors={isScene1 ? yt.sparkColors : tw.sparkColors} seed="dust" opacity={bgIn} />
      </AbsoluteFill>
      <Vignette strength={0.55} />

      <PlatformScene scene={yt} fontFamily={fontFamily} />
      <PlatformScene scene={tw} fontFamily={fontFamily} />

      {frame >= TRANSITION.expand[0] && frame <= TRANSITION.expand[1] ? (
        <CameraMotionBlur shutterAngle={MOTION.motionBlur.shutterAngle} samples={MOTION.motionBlur.samples}>
          <CircleTransition />
        </CameraMotionBlur>
      ) : (
        <CircleTransition />
      )}

      <Grain opacity={0.03} />
    </AbsoluteFill>
  );
};
