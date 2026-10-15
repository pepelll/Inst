import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {CameraMotionBlur} from '@remotion/motion-blur';
import {cameraFor} from '../camera';
import {COLORS, LAYOUT, MOTION, MOTION_BLUR_WINDOWS, SceneConfig} from '../config';
import {LogoMorphToAvatar} from '../components/LogoMorphToAvatar';
import {SparkBurst} from '../components/Particles';
import {TextReveal} from '../components/TextReveal';

const inBlurWindow = (frame: number) => MOTION_BLUR_WINDOWS.some(([a, b]) => frame >= a && frame <= b);

/** One platform scene: logo -> avatar hero, caption, nick and spark burst. */
export const PlatformScene: React.FC<{scene: SceneConfig; fontFamily: string}> = ({scene, fontFamily}) => {
  const frame = useCurrentFrame();
  const {t} = scene;
  if (frame < t.visibleFrom || frame >= t.visibleTo) return null;
  const cam = cameraFor(frame, scene);

  const hero = <LogoMorphToAvatar scene={scene} />;

  return (
    <AbsoluteFill>
      {inBlurWindow(frame) ? (
        <CameraMotionBlur shutterAngle={MOTION.motionBlur.shutterAngle} samples={MOTION.motionBlur.samples}>
          {hero}
        </CameraMotionBlur>
      ) : (
        hero
      )}

      <AbsoluteFill style={{transform: `scale(${cam.hero})`}}>
        <SparkBurst
          start={t.morph + 10}
          x={LAYOUT.centerX}
          y={LAYOUT.avatarY}
          innerRadius={LAYOUT.avatarSize / 2 + LAYOUT.ringGap}
          colors={scene.sparkColors}
          seed={scene.id}
        />
      </AbsoluteFill>

      <AbsoluteFill style={{transform: `translateY(${cam.textY}px) scale(${cam.text})`}}>
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            top: LAYOUT.captionY,
            transform: 'translateY(-50%)',
          }}
        >
          <TextReveal
            lines={scene.captionLines}
            start={t.captionIn}
            exitAt={t.textExit}
            highlight={scene.highlight}
            highlightColor={scene.brand}
            fontFamily={fontFamily}
            fontSize={LAYOUT.captionSize}
            fontWeight={LAYOUT.captionWeight}
            tracking={LAYOUT.captionTracking}
            lineHeight={LAYOUT.captionLineHeight}
            color={COLORS.text}
          />
        </div>
        <div style={{position: 'absolute', left: 0, right: 0, top: LAYOUT.nickY, transform: 'translateY(-50%)'}}>
          <TextReveal
            lines={[scene.nick]}
            start={t.nickIn}
            exitAt={t.textExit === null ? null : t.textExit + 2}
            fontFamily={fontFamily}
            fontSize={LAYOUT.nickSize}
            fontWeight={LAYOUT.nickWeight}
            tracking={LAYOUT.nickTracking}
            stagger={5}
            duration={26}
            color={COLORS.text}
          />
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
