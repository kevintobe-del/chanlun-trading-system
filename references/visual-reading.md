# Visual Reading Protocol

Use this whenever the user provides a chart, book figure, screenshot, or local K-line image, and whenever a Chan theory book figure is relevant.

## First Pass

Identify:

- Figure type: definition diagram, schematic model, historical case, operational chart, or indicator/filter chart.
- Visible labels: A/B/C, center boxes, arrows, buy/sell markers, MACD/RSI/volume notes, trendlines.
- Timeframe and symbol if visible.
- What is explicitly drawn versus what you infer.

## Structure Mapping

Map the image into:

1. Inclusion-processed K-line direction if visible.
2. Top/bottom fractals.
3. Strokes.
4. Segments.
5. Center boundaries and center status.
6. Trend/consolidation/transition.
7. Divergence or no divergence.
8. First/second/third buy/sell point.
9. Filters: MACD, RSI, volume, turnover, money flow, MA, trendline.

## Visual Quality Gates

Do not confirm:

- A stroke if resolution is insufficient to see alternating fractals.
- A center without naming the three overlapping components or proxy swings.
- Divergence until the two compared same-level movements are named.
- Third buy/sell before identifying the center and non-return condition.
- Small-turn-big without seeing the last lower-level center break.

## Diagram-Specific Rules

Definition diagrams:

- Extract the rule, not the exact geometry.
- Identify edge cases shown by the author.

Historical charts:

- Separate hindsight labels from real-time valid triggers.
- Ask whether the buy/sell marker was knowable at that bar.

Indicator charts:

- Treat indicators as confirmation only.
- Name the structural movement before interpreting MACD/volume.

## Output Add-On

When image reading is used, add:

```markdown
**图像读取**
- figure_type:
- visible_labels:
- explicit_structure:
- inferred_structure:
- uncertain_points:
- decision_relevance:
```

## Conflict Handling

If caption and chart disagree:

- State the conflict.
- Prefer visible structure for structural judgment.
- Treat caption as author intent but not automatic proof.
- If resolution is insufficient, mark as uncertain.
