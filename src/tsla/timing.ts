// Timing for the TSLA volume insert (frames @ 60 fps). Also exported for the SFX script.
export const TSLA_FPS = 60;
export const TSLA_DURATION = 330; // 5.5 s

export const T = {
  bgIn: [0, 30],
  header: 12,
  baseline: [6, 44],
  candlesIn: 14, // first candle; the rest follow with candleStagger
  candleStagger: 5,
  volumesIn: 90,
  volumeStagger: 3,
  spike: 150, // last volume bar surges
  spikePeak: 172,
  ghostLaunch: 196, // dot leaves the previous close and shoots up
  ghostApex: 234,
  fallStart: 238,
  land: 264, // dot lands on the real close, candle fully drawn
  priceChip: 266,
  sweep: 292, // light sweep up the volume bar
} as const;
