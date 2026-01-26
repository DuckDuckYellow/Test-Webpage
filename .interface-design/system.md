# Newton's Repository Design System

## Direction: The Scout's Desk

Warm, analytical, serious. Like a well-organized scouting binder.

**Who uses this:** FM players who take analysis seriously. They want insights fast and appreciate data density.

**Feel:** Analytical but not cold. Serious but passionate. A craft tool for people who care.

---

## Tokens

### Colors

```css
:root {
  /* Foreground */
  --ink: #1a1a1a;
  --ink-muted: #5c5c5c;
  --ink-faint: #8a8a8a;

  /* Background */
  --paper: #faf8f5;
  --paper-raised: #ffffff;
  --paper-inset: #f0ede8;

  /* Borders */
  --rule: #e5e2dc;
  --rule-light: #f0ede8;
  --rule-strong: #d1cdc5;

  /* Primary - Pitch green */
  --pitch: #3d5a45;
  --pitch-light: #4a6b53;
  --pitch-dark: #2d4433;

  /* Semantic - Traffic lights */
  --verdict-elite: #2d6a4f;
  --verdict-good: #40916c;
  --verdict-average: #cc8b00;
  --verdict-poor: #9d4444;
}
```

### Typography

- Body: Inter or system sans-serif
- Stats: JetBrains Mono or monospace
- Scale: 12/14/16/18/20/24/32px

### Spacing

Base: 4px. Use: 4, 8, 12, 16, 24, 32, 48, 64.

### Depth

Subtle shadows. Borders for structure, shadows for lift.

```css
--shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
--shadow-md: 0 2px 8px rgba(0,0,0,0.06);
--radius-md: 6px;
```

---

## Signature Elements

1. **Verdict stamps** - Bold bordered badges for ELITE/GOOD/AVERAGE/POOR
2. **Monospace stats** - All numbers in monospace
3. **Warm paper** - Off-white backgrounds, never pure white
4. **Pitch green** - Primary accent color
5. **Subtle depth** - Cards lift slightly

## What This Is Not

- No gradients
- No pure white backgrounds
- No heavy borders
- No Bootstrap blue
