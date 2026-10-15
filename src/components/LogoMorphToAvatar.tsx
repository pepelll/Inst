import React from 'react';
import {AbsoluteFill, Img, random, staticFile, useCurrentFrame} from 'remotion';
import {cameraFor} from '../camera';
import {LAYOUT, MOTION, SceneConfig, TRANSITION} from '../config';
import {easeInOut, lerp, progress, pulse, springAt} from '../easing';
import {AvatarRing} from './AvatarRing';
import {Glow} from './Glow';
import {LightSweep} from './LightSweep';
import {LOGO_ASPECT, TW_MASK, TwitchLogo, YT_MASK, YouTubeLogo} from './Logos';

const Logo: React.FC<{scene: SceneConfig; width: number; eyeScaleY: number; color?: string; inner?: string}> = ({
  scene,
  width,
  eyeScaleY,
  color,
  inner,
}) =>
  scene.id === 'youtube' ? (
    <YouTubeLogo width={width} color={color} />
  ) : (
    <TwitchLogo width={width} eyeScaleY={eyeScaleY} color={color} inner={inner} />
  );

/**
 * Platform logo springs in, then morphs into the round avatar:
 * the logo shrinks into a brand-colored disc that grows into the avatar mask.
 */
export const LogoMorphToAvatar: React.FC<{scene: SceneConfig}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {t, brand} = scene;
  if (frame < t.visibleFrom || frame >= t.visibleTo) return null;
  if (t.collapse !== null && frame >= TRANSITION.dotStart) return null; // CircleTransition owns the dot now

  const cam = cameraFor(frame, scene);
  const L = t.logoIn;
  const M = t.morph;

  // ---------- logo ----------
  const logoW = LAYOUT.logoSize;
  const logoH = logoW / LOGO_ASPECT[scene.id];
  const sp = springAt(frame, L, MOTION.spring);
  const logoIn = progress(frame, L, L + 10);
  const morphOut = progress(frame, M, M + 14, easeInOut);
  const logoScale = lerp(0.3, 1, sp) * lerp(1, 0.5, morphOut);
  const logoBlur = (1 - progress(frame, L, L + 14)) * 22 + morphOut * 14;
  const logoOpacity = logoIn * (1 - morphOut);
  const logoGlow = 0.5 + pulse(frame, L + 2, L + 10, L + 34) * 0.7;

  // Twitch extras: single blink and a 4-frame RGB split
  const blinkDown = progress(frame, L + 9, L + 12, easeInOut);
  const blinkUp = progress(frame, L + 12, L + 16, easeInOut);
  const eyeScaleY = scene.id === 'twitch' ? 1 - 0.9 * blinkDown + 0.9 * blinkUp : 1;
  const glitchOn = scene.id === 'twitch' && frame >= L + 3 && frame < L + 7;
  const gj = (k: string) => random(`glitch-${frame}-${k}`) - 0.5;

  // ---------- avatar ----------
  const D = LAYOUT.avatarSize;
  const as = springAt(frame, M + 2, MOTION.spring); // overshoots ~1.05
  const maskD = lerp(Math.min(logoW, logoH) * 0.7, D, as);
  const imgScale = lerp(0.6, 1, as);
  const avatarOpacity = progress(frame, M, M + 6);
  let brandFill = 1 - progress(frame, M + 5, M + 20, easeInOut);
  const ringIn = progress(frame, M + 10, M + 30);
  const ringPulse = pulse(frame, M + 10, M + 17, M + 50);
  let ringOpacity = ringIn;
  let collapseScale = 1;
  if (t.collapse !== null) {
    const cp = progress(frame, t.collapse, t.collapse + TRANSITION.collapseDuration, easeInOut);
    collapseScale = lerp(1, LAYOUT.dotSize / D, cp);
    brandFill = Math.max(brandFill, progress(frame, t.collapse + 1, t.collapse + 6));
    ringOpacity *= 1 - progress(frame, t.collapse, t.collapse + 4);
  }
  const finalBoost = t.collapse === null ? cam.p * 0.25 : 0;
  const haloStrength = (0.55 + ringPulse * 0.6 + finalBoost) * avatarOpacity;
  const ringSize = D + LAYOUT.ringGap * 2 + LAYOUT.ringWidth * 2;

  const logoNode = (color?: string, inner?: string) => (
    <Logo scene={scene} width={logoW} eyeScaleY={eyeScaleY} color={color} inner={inner} />
  );

  return (
    <AbsoluteFill style={{transform: `scale(${cam.hero})`}}>
      <div style={{position: 'absolute', left: LAYOUT.centerX, top: LAYOUT.avatarY}}>
        {/* ---- avatar ---- */}
        {frame >= M ? (
          <div style={{position: 'absolute', transform: `scale(${collapseScale})`, opacity: avatarOpacity}}>
            {/* brand halo behind the avatar */}
            <div
              style={{
                position: 'absolute',
                width: D * 1.9,
                height: D * 1.9,
                left: -D * 0.95,
                top: -D * 0.95,
                borderRadius: '50%',
                background: `radial-gradient(circle, ${brand}AA 0%, ${brand}44 32%, transparent 62%)`,
                filter: 'blur(40px)',
                opacity: Math.min(1, haloStrength) * (maskD / D),
                mixBlendMode: 'screen',
              }}
            />
            <div style={{position: 'absolute', left: -maskD / 2, top: -maskD / 2}}>
              <Glow color={brand} strength={haloStrength * 0.8} radius={46}>
                <div
                  style={{
                    width: maskD,
                    height: maskD,
                    borderRadius: '50%',
                    overflow: 'hidden',
                    position: 'relative',
                    background: brand,
                  }}
                >
                  <Img
                    src={staticFile(scene.avatar)}
                    style={{
                      position: 'absolute',
                      width: D,
                      height: D,
                      left: (maskD - D) / 2,
                      top: (maskD - D) / 2,
                      transform: `scale(${imgScale})`,
                    }}
                  />
                  <div style={{position: 'absolute', inset: 0, background: brand, opacity: brandFill}} />
                  {t.sweeps.map((s) => (
                    <LightSweep key={s} start={s} duration={30} intensity={0.55} />
                  ))}
                </div>
              </Glow>
            </div>
            {ringOpacity > 0.001 ? (
              <div
                style={{
                  position: 'absolute',
                  opacity: ringOpacity,
                  transform: `scale(${lerp(1.14, 1, ringIn) * (maskD / D)})`,
                }}
              >
                <AvatarRing
                  size={ringSize}
                  width={LAYOUT.ringWidth}
                  colors={scene.ring.colors}
                  rotation={frame * scene.ring.degPerFrame}
                  glow={0.45 + ringPulse * 0.9 + finalBoost}
                />
              </div>
            ) : null}
          </div>
        ) : null}

        {/* ---- logo ---- */}
        {logoOpacity > 0.001 ? (
          <div
            style={{
              position: 'absolute',
              left: -logoW / 2,
              top: -logoH / 2,
              opacity: logoOpacity,
              transform: `scale(${logoScale})`,
              filter: logoBlur > 0.05 ? `blur(${logoBlur}px)` : undefined,
            }}
          >
            <Glow color={brand} strength={logoGlow} radius={50}>
              <div style={{position: 'relative', width: logoW, height: logoH}}>
                {logoNode()}
                <LightSweep
                  start={t.logoSweep}
                  duration={28}
                  intensity={0.75}
                  maskImage={scene.id === 'youtube' ? YT_MASK : TW_MASK}
                />
              </div>
            </Glow>
            {glitchOn ? (
              <>
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    transform: `translate(${-12 + gj('r') * 8}px, ${gj('ry') * 4}px)`,
                    mixBlendMode: 'screen',
                    opacity: 0.85,
                  }}
                >
                  {logoNode('#FF2D55', '#FF2D55')}
                </div>
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    transform: `translate(${12 + gj('c') * 8}px, ${gj('cy') * 4}px)`,
                    mixBlendMode: 'screen',
                    opacity: 0.85,
                  }}
                >
                  {logoNode('#00E5FF', '#00E5FF')}
                </div>
                <div
                  style={{
                    position: 'absolute',
                    inset: 0,
                    clipPath: `inset(${40 + gj('b') * 30}% 0 ${44 - gj('b') * 30}% 0)`,
                    transform: `translateX(${gj('s') * 60}px)`,
                  }}
                >
                  {logoNode()}
                </div>
              </>
            ) : null}
          </div>
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
