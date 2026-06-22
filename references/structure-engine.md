# Structure Engine

## Table Of Contents

- Operating sequence
- K-line inclusion
- Fractals
- Strokes
- Segments
- Centers
- Center extension, newborn, expansion
- Quality checks

## Operating Sequence

Use the same sequence every time:

1. Normalize K-lines and handle inclusion.
2. Mark top/bottom fractals.
3. Build strokes.
4. Build segments.
5. Build centers from lower-level trend types or proxy segments.
6. Classify trend/consolidation.
7. Only then discuss divergence and buy/sell points.

If a step is impossible with available data, stop and downgrade to proxy mode.

## K-Line Inclusion

Inclusion means one K-line's high-low range contains or is contained by the adjacent K-line.

Direction-dependent handling:

- In an upward direction, merge by keeping the higher high and higher low.
- In a downward direction, merge by keeping the lower high and lower low.
- If direction is unknown, infer from the nearest non-contained predecessor; if still unclear, mark uncertain and avoid strict stroke judgment.

Operational purpose:

- Remove local noise.
- Make fractals comparable.
- Prevent false strokes caused by nested bars.

Common mistakes:

- Merging inclusion without first identifying direction.
- Using unmerged bars to force extra fractals.
- Treating a one-bar spike as a confirmed stroke without separation.

## Fractals

Top fractal:

- After inclusion processing, the middle K-line has a higher high and higher low than adjacent K-lines.

Bottom fractal:

- After inclusion processing, the middle K-line has a lower low and lower high than adjacent K-lines.

Quality checks:

- Top and bottom fractals must alternate to form strokes.
- Same-kind consecutive fractals: keep the more extreme one.
- Too-close fractals often reflect noise; require minimum separation for proxies.
- A fractal is a structural primitive, not a trade signal by itself.

## Strokes

A stroke connects a valid top and bottom fractal.

Requirements:

- Opposite fractal types.
- Enough K-line separation after inclusion.
- Extremes are not invalidated by a more extreme same-kind fractal before the opposite fractal is confirmed.
- Direction is clear: bottom -> top is up; top -> bottom is down.

Stroke quality:

- `strong`: clear separation, strong price movement, matching volume/force.
- `normal`: valid but not dominant.
- `weak/noisy`: barely separated or heavily overlapped; use only in proxy mode.

Stroke metrics useful for research:

- Bars count.
- Percentage move.
- Slope.
- MACD area in movement direction.
- Volume/amount ratio during impulse and pullback.

## Segments

Segments are higher-order structures made from strokes.

Use strict judgment when data is detailed; otherwise use segment proxies:

- A segment usually requires at least three strokes and a break/confirmation pattern.
- Segment direction depends on the structure of strokes, not a simple moving average.
- A segment's end should be confirmed by destruction of the previous lower-level structure.

Segment proxy for backtests:

- Use alternating stroke sequences.
- Require minimum bars and minimum movement.
- Mark segment start/end with confirmed fractal extremes.
- Record `definition_mode=segment_proxy`.

## Centers

Strict center:

- Overlap of at least three continuous sublevel trend types.

Segment proxy center:

- Overlap of at least three continuous sublevel segments or strokes.
- Let `zg = min(highs)` and `zd = max(lows)` for the overlapping components.
- Valid overlap requires `zd <= zg`.

Center fields:

- `start/end`: date or index range.
- `zg/zd`: overlap boundaries.
- `gg/dd`: full high/low range.
- `components`: named sublevel movements.
- `state`: forming, oscillating, extension, newborn, expansion, broken_up, broken_down.

## Center Extension

Extension occurs when additional same-level movements keep returning to or overlapping the same center.

Operational meaning:

- Treat as center oscillation until true departure.
- Do not call a new trend merely because price left once.
- Short-difference trades inside extension require smaller-level skill.

## Newborn Center

A new center is born when a same-level center forms away from the old center after departure.

Implication:

- Two non-overlapping same-level centers in the same direction support trend classification.
- Watch for divergence on the movement leaving the second center.

## Center Expansion

Expansion occurs when structures that appeared separated overlap at a higher level.

Implication:

- A supposed trend can degrade into higher-level consolidation.
- Prior buy/sell points should be re-evaluated at the expanded level.
- Do not keep operating on the smaller level if the higher-level center now controls price.

## Break And Pullback/Rebound

Upward leave:

- Price or sublevel segment leaves above `zg`.
- A valid third buy requires pullback not re-entering the center in the chosen definition.

Downward leave:

- Price or sublevel segment leaves below `zd`.
- A valid third sell requires rebound not re-entering the center.

Quality:

- Clean leave with moderate/strong force is better.
- Overheated leave plus immediate high-volume reversal is suspect.
- Weak leave without lower-level confirmation is only `center_breakout_candidate`.

## Quality Checks

Before accepting structure:

- Are inclusion rules applied?
- Are fractals alternating?
- Are strokes separated enough?
- Are compared segments on the same level?
- Is the center built from named components?
- Is price location relative to `zg/zd` clear?
- Is the current state center oscillation, transition, or trend?
- Is the signal definition strict or proxy?
