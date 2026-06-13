# Brand Guardian → Deck Builder handoff

**Brand:** Meridian Analytics
**Prepared by:** Brand Guardian
**Consumed by:** Deck Builder (transcribed verbatim into the slidekit IR `theme:` block)

This is the upstream artifact in the orchestrated pipeline
`Brand Guardian → Visual Storyteller → Deck Builder → slidekit build`.
It carries exactly the four things the Deck Builder's "From Brand Guardian"
seam expects: palette roles, a type scale, a font, and a motif. Nothing here
is raw hex used inside slide bodies — these are *role* definitions the Deck
Builder references by name.

```yaml
theme:
  palette:                 # role-keyed, hex values
    primary: "#16504B"     # deep teal — headings, title-slide ground
    surface: "#FFFFFF"     # slide background
    accent:  "#E2A03F"     # amber — icons, emphasis marks
    text:    "#1C1C28"     # near-black body text
    muted:   "#8A8A9A"     # page numbers / captions
  type_scale:              # points; body MUST be >= 32 (hard slidekit floor)
    title:  58             # within 54-66
    header: 42             # within 40-44
    body:   34             # within 32-36
    caption: 24            # within 24-26
  font: calibri            # metric-safe set only
  motif: minimal
```

## Brand notes for the Deck Builder
- The body size is **34pt**, comfortably above slidekit's hard 32pt floor — no
  conflict to flag back.
- `calibri` is in slidekit's metric-safe set, so it will not raise `E_FONT`.
- Amber (`accent`) is reserved for icons and emphasis, never for body text on
  the white `surface` (contrast).
