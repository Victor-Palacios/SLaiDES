# Layout feedback — slidekit

_Generated from `FEEDBACK.yaml` by `scripts/render_feedback.py` — do not hand-edit. `FEEDBACK.yaml` is the source of truth; file new comments via the feedback website (see web/README.md). The nightly reads `open` items, queues them on the board, and marks them `done`._

**open** 0 · **done** 16 · **wontfix** 1 · _last change 2026-07-02_

## Done (16)

| ID | Layout | Sev | Comment | Notes |
|---|---|---|---|---|
| FB-001 | icon-text-rows | med | remove the large bubbles | issue #9: removed accent 'bubble' disc; icon-text-rows is heading+body full-width |
| FB-002 | stat-callout | med | alignment is wrong for middle column (top  most text should align with right and left text) | issue #10: uniform block height + shared top y so every column's value/label align |
| FB-003 | image-half-bleed | med | text on the bottom right looks odd - should come after the first block of text (too much white space between text) | issue #11: removed expanding spacer so the second text block follows the first |
| FB-004 | card-grid | med | remove bubbles | issue #12: removed accent 'bubble' disc from cards |
| FB-005 | feature-list | med | get rid of bubbles | issue #13: removed accent 'bubble' disc; feature-list is heading+body full-width |
| FB-006 | code | med | delete this layout | issue #14: repurposed checklist into the new dark terminal/IDE 'code' layout (operator chose repurpose over delete) |
| FB-008 | title-slide | med | 👎 remove distracting subheader | done T-054 — subtitle stripped from title-slide specimen (optional field kept) |
| FB-009 | comparison-columns | med | 👎 delete this slide layout - redundant with "comparison-columns" | done T-055 — comment was about the retired two-column component; the two-column layout was deleted (model/handler/registry/scaffold/examples/goldens) as redundant, and comparison-columns now anchors the two-column family. Component retargeted to comparison-columns here because the catalog no longer contains two-column. |
| FB-010 | icon-text-rows | med | 👎 Can't read the subtext like "high standards..." | done T-056 — body box was shorter than one line; paired heading+body on 0.1" inner gap, guaranteed >= one line |
| FB-011 | stat-callout | med | 👎 get rid of the small grey text - it's distracting | done T-057 — muted subtext stripped from stat-callout specimen (optional field kept) |
| FB-012 | comparison-columns | med | 👎 Make it 3 items after the headers of legacy platform and modern stack with more space between items | done T-058 — specimen trimmed to 3 items per column; handler distributes items to fill the column, so 3 items get taller boxes and clear space between them (golden captures new geometry) |
| FB-013 | timeline | med | 👎 foundation text gets cut off at the end (set limit for how many words can appear - the other columns are perfect) | done T-059 — new W_TIMELINE_BALANCE advisory flags any timeline column that wraps to more lines than its siblings (deterministic, no render); specimen Q1 trimmed to balance all four columns at 4 lines |
| FB-014 | section-divider | med | 👎 Change the position of the number to be a bit higher such that the text is center-aligned instead of the number | done T-060 — section-divider centres the title; number rides above (center_on) |
| FB-015 | agenda | med | 👎 Need more space or something because letters like g, p, and y have their bottom half missing. | done T-061 — web-preview emitter pinned line-height + dropped vertical padding + overflow visible (single-line-row descender clip class) |
| FB-016 | quote-opener | med | 👎 not all the text is displayed correctly. might be a spacing issue | done T-062 — same root cause as FB-015; fixed by the emitter change |
| FB-017 | big-number | med | 👎 remove final line | done T-063 — context line stripped from big-number specimen (optional field kept) |

## Won't fix (1)

| ID | Layout | Sev | Comment | Notes |
|---|---|---|---|---|
| FB-007 | title-slide | med | 👎 remove the distracting subheader | duplicate of FB-008 (same comment submitted twice while testing the website) |

