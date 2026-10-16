import React from 'react';
import {Composition} from 'remotion';
import {ArutPromo} from './ArutPromo';
import {DURATION_IN_FRAMES, FPS, HEIGHT, WIDTH} from './config';
import {TeslaVolume} from './tsla/TeslaVolume';
import {TSLA_DURATION, TSLA_FPS} from './tsla/timing';

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="ArutPromo"
      component={ArutPromo}
      durationInFrames={DURATION_IN_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
    <Composition
      id="TeslaVolume"
      component={TeslaVolume}
      durationInFrames={TSLA_DURATION}
      fps={TSLA_FPS}
      width={1080}
      height={1920}
    />
  </>
);
