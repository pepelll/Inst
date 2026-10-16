// Real daily TSLA bars (NASDAQ), volume in millions of shares.
// Oct 6-15: StockAnalysis (S&P Global Market Intelligence).
// Oct 16: intraday snapshot (~15:04 ET) from Yahoo Finance / Finviz - update with the official close and re-render.
export type Bar = {date: string; o: number; h: number; l: number; c: number; v: number};

export const BARS: Bar[] = [
  {date: '6 окт', o: 381.98, h: 383.33, l: 378.52, c: 380.68, v: 27.74},
  {date: '7 окт', o: 378.45, h: 382.35, l: 374.43, c: 377.81, v: 25.54},
  {date: '8 окт', o: 374.12, h: 375.96, l: 368.03, c: 375.0, v: 28.15},
  {date: '9 окт', o: 382.38, h: 388.56, l: 379.71, c: 382.7, v: 38.76},
  {date: '12 окт', o: 382.61, h: 382.7, l: 377.58, c: 378.03, v: 19.96},
  {date: '13 окт', o: 372.33, h: 377.05, l: 371.3, c: 375.23, v: 18.22}, // Roadster event announced
  {date: '14 окт', o: 371.16, h: 371.39, l: 363.82, c: 367.16, v: 29.44},
  {date: '15 окт', o: 360.57, h: 363.75, l: 355.23, c: 362.44, v: 26.71}, // unveil after the close
  {date: '16 окт', o: 369.04, h: 370.58, l: 349.8, c: 349.8, v: 50.24}, // reaction day
];

// The last bars carry the story; everything before is dimmed context.
export const FOCUS_FROM = BARS.length - 3;
export const LAST = BARS[BARS.length - 1];
export const PREV = BARS[BARS.length - 2];
export const PRICE_CHANGE = (LAST.c / PREV.c - 1) * 100;
