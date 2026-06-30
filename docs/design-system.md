# Oscilloscope design system

## Visual premise

Anime ratings are treated as sampled signals. The interface borrows restrained elements from an oscilloscope rather than imitating a hardware panel literally.

## Tokens

- Background: deep navy `#07131f`
- Surface: blue-black `#0c1c29`
- Primary signal: mint `#7ef7c7`
- Secondary channel: blue `#73b7ff`
- Alert/accent: pink `#ff7a9d`
- Caution/new signal: amber `#f6d36d`
- Grid and borders use low-opacity mint/blue rather than solid gray.

## Typography

- Chinese interface: system sans-serif, prioritizing PingFang SC and Microsoft YaHei.
- Scores, timestamps, formulas, and signal labels: system monospace.
- English overlines use uppercase text with generous tracking.

## Interaction principles

- Always label preview or stale data explicitly.
- Never use a missing score as zero.
- Show source, sample time, population, and weighting near computed scores.
- Use color together with text or symbols; do not encode state with color alone.
- Phase 1 is desktop-first with a minimum layout width of 1080px.
