import React from 'react';
import {Composition} from 'remotion';
import {ArutPromo} from './ArutPromo';
import {DURATION_IN_FRAMES, FPS, HEIGHT, WIDTH} from './config';

export const RemotionRoot: React.FC = () => (
  <Composition
    id="ArutPromo"
    component={ArutPromo}
    durationInFrames={DURATION_IN_FRAMES}
    fps={FPS}
    width={WIDTH}
    height={HEIGHT}
  />
);
