# Layout feedback — slidekit

_Generated from `FEEDBACK.yaml` by `scripts/render_feedback.py` — do not hand-edit. `FEEDBACK.yaml` is the source of truth; file new comments via the feedback website (see web/README.md). The nightly reads `open` items, queues them on the board, and marks them `done`._

**open** 19 · **done** 89 · **wontfix** 1 · _last change 2026-07-22_

## Open (19)

| ID | Layout | Where | Sev | Comment | Notes |
|---|---|---|---|---|---|
| FB-091 | title-slide | claude-code-for-data-scientists #1 | med | 👎 Make the Claude Code font much bigger. Let's use the 3rd slide's beige color for all slide titles/headlines if there is no other color present. Then remove the subheader. |  |
| FB-092 | agenda | claude-code-for-data-scientists #2 | med | 👎 remove this slide from this deck |  |
| FB-093 | numbered-steps | claude-code-for-data-scientists #6 | med | 👎 remove this slide from this deck |  |
| FB-094 | code | claude-code-for-data-scientists #7 | med | 👎 a first session --> Terminal Use |  |
| FB-095 | nested-circles | claude-code-for-data-scientists #10 | med | 👎 remove this slide from this deck |  |
| FB-096 | two-panel-list | claude-code-for-data-scientists #11 | med | 👎 Use the beige color (slide 3) for Claude not grey |  |
| FB-097 | table-slide | claude-code-for-data-scientists #12 | med | 👍 add a slide that explains init and claude -p |  |
| FB-098 | bullet-list | layout / theme | med | 👎 don't have any lines with text that overflows to the next line. |  |
| FB-099 | comparison-matrix | claude-code-for-data-scientists #16 | med | 👎 remove the Best for row and it's associated items |  |
| FB-100 | bullet-list | claude-code-for-data-scientists #17 | med | 👎 remove slide from deck |  |
| FB-101 | bullet-list | claude-code-for-data-scientists #23 | med | 👎 remove the last line |  |
| FB-102 | code | layout / theme | med | 👎 The grey title must be title capitalized and easier to read - this bold font looks awkward. |  |
| FB-103 | bullet-list | claude-code-for-data-scientists #27 | med | 👍 add a slide of concrete examples after this and how MCP is better than no MCP. |  |
| FB-104 | table-slide | claude-code-for-data-scientists #28 | med | 👎 Servers You Can (normally) Connect to |  |
| FB-105 | section-divider | claude-code-for-data-scientists #29 | med | 👎 Make Claude Yours --> Customize Claude |  |
| FB-106 | bullet-list | claude-code-for-data-scientists #31 | med | 👍 next slide should be an example of what things to put in the md and then another slide of "beware" or common problems when using a Claude.md file |  |
| FB-107 | two-panel-list | claude-code-for-data-scientists #33 | med | 👎 CLAUDE.md vs Skills --> CLAUDE.md vs Skills.md (same for column 2: Skills.md) |  |
| FB-108 | question | claude-code-for-data-scientists #34 | med | 👎 What would you analyze if the boilerplate wrote itself? --> Let's build our visualization library with Claude + Github using our phones! |  |
| FB-109 | title-slide | claude-code-for-data-scientists #35 | med | 👎 remove this slide and add 2 slides about Claude Cowork and 1 slide on Claude Artifacts and 1 slide on  Memory > Search and reference chats. |  |

## Done (89)

| ID | Layout | Where | Sev | Comment | Notes |
|---|---|---|---|---|---|
| FB-001 | icon-text-rows | layout / theme | med | remove the large bubbles | issue #9: removed accent 'bubble' disc; icon-text-rows is heading+body full-width |
| FB-002 | stat-callout | layout / theme | med | alignment is wrong for middle column (top  most text should align with right and left text) | issue #10: uniform block height + shared top y so every column's value/label align |
| FB-003 | image-half-bleed | layout / theme | med | text on the bottom right looks odd - should come after the first block of text (too much white space between text) | issue #11: removed expanding spacer so the second text block follows the first |
| FB-004 | card-grid | layout / theme | med | remove bubbles | issue #12: removed accent 'bubble' disc from cards |
| FB-005 | icon-text-rows | layout / theme | med | get rid of bubbles | issue #13: removed accent 'bubble' disc; feature-list was heading+body full-width. [Component re-pointed feature-list -> icon-text-rows after FB-049 deleted feature-list.] |
| FB-006 | code | layout / theme | med | delete this layout | issue #14: repurposed checklist into the new dark terminal/IDE 'code' layout (operator chose repurpose over delete) |
| FB-008 | title-slide | layout / theme | med | 👎 remove distracting subheader | done T-054 — subtitle stripped from title-slide specimen (optional field kept) |
| FB-009 | comparison-columns | layout / theme | med | 👎 delete this slide layout - redundant with "comparison-columns" | done T-055 — comment was about the retired two-column component; the two-column layout was deleted (model/handler/registry/scaffold/examples/goldens) as redundant, and comparison-columns now anchors the two-column family. Component retargeted to comparison-columns here because the catalog no longer contains two-column. |
| FB-010 | icon-text-rows | layout / theme | med | 👎 Can't read the subtext like "high standards..." | done T-056 — body box was shorter than one line; paired heading+body on 0.1" inner gap, guaranteed >= one line |
| FB-011 | stat-callout | layout / theme | med | 👎 get rid of the small grey text - it's distracting | done T-057 — muted subtext stripped from stat-callout specimen (optional field kept) |
| FB-012 | comparison-columns | layout / theme | med | 👎 Make it 3 items after the headers of legacy platform and modern stack with more space between items | done T-058 — specimen trimmed to 3 items per column; handler distributes items to fill the column, so 3 items get taller boxes and clear space between them (golden captures new geometry) |
| FB-013 | timeline | layout / theme | med | 👎 foundation text gets cut off at the end (set limit for how many words can appear - the other columns are perfect) | done T-059 — new W_TIMELINE_BALANCE advisory flags any timeline column that wraps to more lines than its siblings (deterministic, no render); specimen Q1 trimmed to balance all four columns at 4 lines |
| FB-014 | section-divider | layout / theme | med | 👎 Change the position of the number to be a bit higher such that the text is center-aligned instead of the number | done T-060 — section-divider centres the title; number rides above (center_on) |
| FB-015 | agenda | layout / theme | med | 👎 Need more space or something because letters like g, p, and y have their bottom half missing. | done T-061 — web-preview emitter pinned line-height + dropped vertical padding + overflow visible (single-line-row descender clip class) |
| FB-016 | pull-quote | layout / theme | med | 👎 not all the text is displayed correctly. might be a spacing issue | done T-062 — same root cause as FB-015; fixed by the emitter change. [Component re-pointed quote-opener -> pull-quote after FB-048 deleted quote-opener.] |
| FB-017 | big-number | layout / theme | med | 👎 remove final line | done T-063 — context line stripped from big-number specimen (optional field kept) |
| FB-018 | title-slide | layout / theme | med | 👎 left-center align the title | done — title(+subtitle) block now vertically centred on the full content area, left-aligned |
| FB-019 | big-number | layout / theme | med | 👎 Make the number bigger (maybe double or 1.5 bigger) and center everything | done — value 1.75x title tier (105pt default), whole stack centred with a centred accent rule (left bar dropped) |
| FB-020 | bullet-list | layout / theme | med | 👎 3 items instead of 4 | done — specimen trimmed to 3 items |
| FB-021 | code | layout / theme | med | 👎 Show actual example like “hello world” so I can see text color change | done — specimen is now a hello-world program AND the web preview renderer was fixed to honour per-node text colours (it silently dropped them, so code colours never showed) |
| FB-022 | two-panel-list | layout / theme | med | 👎 too similar to before after slide type - delete this and give the before after a more versatile name | done — pros-cons deleted; before-after renamed two-panel-list (left/right panels, right accented) covering before/after, pros/cons, old/new |
| FB-023 | this-vs-that | layout / theme | med | 👎 Proportions are off for VS size and its position is strange | done — VS badge 0.75" (was 0.9"), 'VS' centred inside it on both axes, badge centred on the value+label block, columns centre-aligned; preview renderer previously dropped the badge box entirely |
| FB-024 | kpi-grid | layout / theme | med | 👎 spacing is bad | done — intra-tile gaps 0.3"->0.12", rule centred under the value, tile text centre-aligned |
| FB-025 | chart-with-insight | layout / theme | med | 👎 delete this | done — chart-slide deleted; chart-with-insight is the surviving chart layout |
| FB-026 | bullet-list | layout / theme | med | 👎 never use bullets | done — square list markers removed everywhere (bullet-list, two-panel-list, swot, roadmap items); flush-left lines with a thin accent/panel-colour rule as the non-text mark; codified as a no-bullets test |
| FB-027 | code | layout / theme | med | 👎 the text color needs to match modern IDE color usage for python code | done — deterministic per-token highlighter, VS Code Dark+ palette (keywords/strings/comments/functions/numbers), background #1E1E1E; each colour run is its own measured node so the linter still proves fit |
| FB-028 | this-vs-that | layout / theme | med | 👎 Use all black text, these colors look jarring. The vs should not have a box around it. | done — values/labels in the default text colour, VS is a bare muted caption centred between the columns (badge box removed); slide is deliberately text-only (lint-exempted) |
| FB-029 | pull-quote | layout / theme | med | 👎 delete - too similar to another slide layout | done — testimonial deleted (redundant with pull-quote); recommender routes quote+portrait to pull-quote |
| FB-030 | bullet-list | layout / theme | med | 👎 Drop the orange, ugly color line | Dropped the accent rule under the title (engine); bullet-list is now pure typography (title + flush-left items) and is W_TEXT_ONLY-exempt in the linter. Intent test updated. |
| FB-031 | code | layout / theme | med | 👎 I want the background color to be as it was in the previous version, but the colors look good for the text | _CODE_BG returned to the original deep-teal #0C1A1C (pre-FB-027 panel); VS Code Dark+ token colours kept unchanged. Pinned by test_code_background_is_the_original_deep_teal. |
| FB-032 | this-vs-that | layout / theme | med | 👎 make the VS a little larger | Bare VS stepped up from caption tier (25pt) to body tier (34pt), still muted/bold; middle gutter widened 0.75"->1.0" so it fits with standard insets. |
| FB-033 | table-slide | layout / theme | med | 👎 I think the headers should be a little bit closer to the line | Header row now sits a tight 0.12" above the accent rule (was the full 0.3" gap); headers+rule share group_id table_head so the linter treats the pair as intentional. |
| FB-034 | metric-comparison | layout / theme | med | 👎 The alignment is wrong | Root cause: each column vertically centred itself on its OWN wrapped-label height, so the big values drifted to different heights. Now all columns share one rhythm (common value/label/chip rows sized to the tallest label) and value/label/chip are centred within each column. |
| FB-035 | process-steps | layout / theme | med | 👎 reimagine this slide | Reimagined: filled chip badges replaced by large accent numerals (01/02/03) over thin accent rules, then bold label + body — the typographic motif from the approved agenda/kpi-grid layouts. |
| FB-036 | roadmap | layout / theme | med | 👎 The black texts have too much white space between them | Items now PACK at the minimum 0.3" rhythm under each phase band instead of being distributed across the full lane height (the distribution read as disconnected floating lines). |
| FB-037 | swot | layout / theme | med | 👎 reimagine this slide | Reimagined: hairline MUTED cross (was heavy accent rules), quadrant labels bold and centred both ways in their cells, axis captions centred; new optional highlight: <idx> field puts the accent on at most ONE quadrant (per the FB-039 rule that matrices highlight items, not scaffolding). [Component re-pointed matrix-2x2 -> swot after FB-044 deleted matrix-2x2.] |
| FB-038 | swot | layout / theme | med | 👎 One item per category | IR now enforces exactly one statement per category (max_length=1 on all four quadrant lists); the single item renders at full body tier (caption-tier density compromise retired). Specimen updated. |
| FB-039 | comparison-matrix | layout / theme | med | 👎 any matrix should always only highlight one or two items within the matrix not the categories so the coloring is off | Reimagined: coloured header/criteria boxes removed — options are plain bold primary text over a thin accent rule (table-slide motif), criteria plain bold text, cells plain text. New highlights: [[row, col], ...] field (max 2) renders the winning cell(s) as accent chips — the only colour in the matrix body. |
| FB-040 | card-grid | layout / theme | med | 👎 delete this one | team-grid DELETED per operator (model, layout, registry, specimen, golden, recommender). logo-wall is now the labeled-image-grid anchor; people intros fall back to card-grid. (Item retargeted to logo-wall, then to card-grid after FB-046 deleted logo-wall too.) |
| FB-041 | image-half-bleed | layout / theme | med | 👎 delete this one | image-full-bleed DELETED per operator; image-half-bleed is the surviving image layout and the recommender routes single images there. (Retargeted for validator.) |
| FB-042 | image-half-bleed | layout / theme | med | 👎 delete this one | image-grid DELETED per operator; multi-image content routes to image-half-bleed. (Retargeted for validator.) |
| FB-043 | this-vs-that | layout / theme | med | 👎 The VS a little bigger | VS stepped up again: body tier (34pt) -> header tier (42pt), still muted/bold; middle gutter widened 1.0"->1.25" so it clears the overflow check with standard insets. |
| FB-044 | swot | layout / theme | med | 👎 delete this slide | matrix-2x2 DELETED per operator (model, layout, registry, specimen, golden, recommender) — one round after its FB-037 reimagining. swot is the surviving 2x2; generic axes content falls back to card-grid. (Retargeted to swot because the validator requires a catalog component.) |
| FB-045 | comparison-matrix | layout / theme | med | 👎 too many colors just stick with the red and black | Option headers now render in the DEFAULT text colour instead of brand primary (the primary tint read as a third colour), and the specimen palette sets primary to the text tone — the slide is literally red (rule + highlight chips) and black (everything else). |
| FB-046 | card-grid | layout / theme | med | 📝 delete this slide layout | logo-wall DELETED per operator note, closing the labeled-image-grid family. Logo content falls back to card-grid label cards in the recommender. (Retargeted for validator.) |
| FB-047 | section-divider | layout / theme | med | Delete the statement layout | statement DELETED per operator chat request. It was the emphasis-stack anchor, so the family re-anchored on section-divider (variants re-pointed). A one-line manifesto/closing is covered by title-slide or big-number. (Entry filed against the new anchor because the validator requires a catalog component.) |
| FB-048 | pull-quote | layout / theme | med | Delete the quote-opener layout | quote-opener DELETED per operator chat request; pull-quote is the surviving quote layout and the recommender routes all quotes there. (Retargeted for validator.) |
| FB-049 | icon-text-rows | layout / theme | med | Delete the feature-list layout | feature-list DELETED per operator chat request; icon-text-rows (its family anchor) covers icon + heading + body rows and the recommender routes icon features there. (Retargeted for validator.) |
| FB-050 | title-slide | layout / theme | med | 👎 Remove the black text | applied 2026-07-21 (deck content + reusable layout update) |
| FB-051 | process-steps | layout / theme | med | 👎 Make it 4 items instead of 5 | applied 2026-07-21 (deck content + reusable layout update) |
| FB-052 | numbered-steps | layout / theme | med | 👎 The number size needs to align with the blue text size. Make the blue text size bigger to match the number. | applied 2026-07-21 (deck content + reusable layout update) |
| FB-053 | pull-quote | designing-your-own-eda-library #4 | med | 👎 I only want the quote - I think there is a different slide layout we can use to remove "mantra" part | applied 2026-07-21 (deck content + reusable layout update) |
| FB-054 | code | layout / theme | med | 👎 "What we're building" need to be bigger font size (exceed the code font size) | applied 2026-07-21 (deck content + reusable layout update) |
| FB-055 | two-panel-list | layout / theme | med | 👎 The grey / gold words to align with their colored bar underneath them (left-aligned) | applied 2026-07-21 (deck content + reusable layout update) |
| FB-056 | comparison-columns | designing-your-own-eda-library #8 | med | 👎 Remove "run:" and "use:" | applied 2026-07-21 (deck content + reusable layout update) |
| FB-057 | definition | designing-your-own-eda-library #9 | med | 👎 This should be "library" and it's definition and needs to be slide 8 (swap slide 8 with slide 9) | applied 2026-07-21 (deck content + reusable layout update) |
| FB-058 | bullet-list | designing-your-own-eda-library #10 | med | 👎 3 items - not 4 | applied 2026-07-21 (deck content + reusable layout update) |
| FB-059 | section-divider | designing-your-own-eda-library #12 | med | 👍 add a slide after this defining "API" and then another defining slide with "MVP" - minimum viable product | applied 2026-07-21 (deck content + reusable layout update) |
| FB-060 | code | designing-your-own-eda-library #13 | med | 👎 the grey words need to be "the simplest API" | applied 2026-07-21 (deck content + reusable layout update) |
| FB-061 | two-panel-list | designing-your-own-eda-library #14 | med | 👎 move boring to the left and reduce to 3 items for both columns | applied 2026-07-21 (deck content + reusable layout update) |
| FB-062 | bullet-list | layout / theme | med | 👎 for layout: spacing seems odd. for slide in deck, not layout: title should say "MVP Input: Pandas dataframe only".) | slide retitled; bullet-list packing fixed so few items no longer float (engine _layout_bullet_list) |
| FB-063 | code | designing-your-own-eda-library #16 | med | 👎 Grey text should say "MVP Output: Plain objects only" | applied 2026-07-21 (deck content + reusable layout update) |
| FB-064 | two-panel-list | designing-your-own-eda-library #17 | med | 👎 remove this slide from deck | applied 2026-07-21 (deck content + reusable layout update) |
| FB-065 | file-tree | layout / theme | med | 👎 I don't like the coloring (make it look more like the usual coloring for this topic) | applied 2026-07-21 (deck content + reusable layout update) |
| FB-066 | code | designing-your-own-eda-library #22 | med | 👎 remove this slide from the deck | applied 2026-07-21 (deck content + reusable layout update) |
| FB-067 | bullet-list | designing-your-own-eda-library #28 | med | 👎 drop to 3 functions instead (remove the last one) | applied 2026-07-21 (deck content + reusable layout update) |
| FB-068 | two-panel-list | designing-your-own-eda-library #33 | med | 👎 do needs to be the first column and then don't | applied 2026-07-21 (deck content + reusable layout update) |
| FB-069 | two-panel-list | designing-your-own-eda-library #6 | med | 👎 "build now" on left, "skip for now" on right | applied 2026-07-21 (deck edit) |
| FB-070 | definition | designing-your-own-eda-library #8 | med | 👎 delete "— not a file you run top-to-bottom. Ours inspects a dataset; it does not clean it." | applied 2026-07-21 (deck edit) |
| FB-071 | bullet-list | designing-your-own-eda-library #11 | med | 👎 remove (Module 5) | applied 2026-07-21 (deck edit) |
| FB-072 | definition | designing-your-own-eda-library #13 | med | 👎 remove: — the surface you design on purpose. Keep it small; it is what people remember. then I want you to add one line of 1 or 2 examples. | applied 2026-07-21 (deck edit) |
| FB-073 | definition | designing-your-own-eda-library #14 | med | 👎 delete: Ship it, then grow. | applied 2026-07-21 (deck edit) |
| FB-074 | title-slide | designing-your-own-eda-library #1 | med | 👍 Build Your First Library has a nice color - make sure that my font is primarily this color throughout the whole deck (sometimes it's black which I don't like if that's the only color on the screen). | applied 2026-07-21 (deck theme: text colour set to the python blue) |
| FB-075 | process-steps | designing-your-own-eda-library #2 | med | 👎 change the gold to match the blue font seen here. (in general make sure these 2 items match in color when using this layout style) | applied 2026-07-21 (process-steps: numeral+rule now primary, matching the label) |
| FB-076 | numbered-steps | layout / theme | med | 👎 change the gold to match the blue font seen here. (in general make sure these 2 items match in color when using this layout style) | applied 2026-07-21 (numbered-steps: numeral now primary, matching the heading) |
| FB-077 | code | layout / theme | med | 👎 the grey font is hard to read - choose a different font style or play with unbolding, etc.; just make it easier to read. | applied 2026-07-21 (code title colour brightened to the light foreground) |
| FB-078 | two-panel-list | designing-your-own-eda-library #6 | med | 👎 Build now grey font should be the same blue font as header - make gold this grey color | applied 2026-07-21 (two-panel-list: left=primary, right=muted; gold dropped) |
| FB-079 | definition | designing-your-own-eda-library #13 | med | 👎 Change to: Application Programming Interface - The public interface of the library. The functions, classes, and their signatures that users call. For example: eda.summarize(df), eda.missing(df). | applied 2026-07-21 (API definition expanded per operator text) |
| FB-080 | code | designing-your-own-eda-library #18 | med | 👎 Change slide layout to just give examples of plain objects (dictionary, int, string, etc.). I don't need to see an actual dictionary. | applied 2026-07-21 (slide now names plain object types, no literal dict) |
| FB-081 | file-tree | designing-your-own-eda-library #21 | med | 👎 remove (src layout) | applied 2026-07-21 (removed '(src layout)' from the title) |
| FB-082 | two-panel-list | designing-your-own-eda-library #22 | med | 👍 add a slide after this reasoning why hyphens and underscores (what value? what importance?) | applied 2026-07-21 (added 'Why the names differ' slide) |
| FB-083 | bullet-list | designing-your-own-eda-library #25 | med | 👍 add a slide after that states what happens when these mistakes are made. | applied 2026-07-21 (added 'What each mistake causes' table) |
| FB-084 | code | designing-your-own-eda-library #27 | med | 👎 no need for the grey title | applied 2026-07-21 (removed the grey title from the summarize() slide) |
| FB-085 | code | designing-your-own-eda-library #29 | med | 👎 show a simple output example | applied 2026-07-21 (added a simple output example under missing()) |
| FB-086 | code | designing-your-own-eda-library #31 | med | 👍 add a slide explaining this slide | applied 2026-07-21 (added 'What that file does' explainer slide) |
| FB-087 | two-panel-list | designing-your-own-eda-library #33 | med | 👍 add a slide for the final row to compare those 2 concepts. also add a slide for "signatures". | applied 2026-07-21 (added one-job-vs-everything compare + Signature definition) |
| FB-088 | bullet-list | designing-your-own-eda-library #35 | med | 👎 remove: Replaces old setup.py workflows. | applied 2026-07-21 (removed 'Replaces old setup.py workflows.') |
| FB-089 | code | designing-your-own-eda-library #36 | med | 👎 A minimal pyproject.toml --> Minimal pyproject.toml | applied 2026-07-21 (title 'A minimal pyproject.toml' -> 'Minimal pyproject.toml') |
| FB-090 | table-slide | designing-your-own-eda-library #37 | med | 👎 Bring Means column and examples closer to the Version column (too much white space between them) | applied 2026-07-21 (table-slide columns now content-width, packed left) |

## Won't fix (1)

| ID | Layout | Where | Sev | Comment | Notes |
|---|---|---|---|---|---|
| FB-007 | title-slide | layout / theme | med | 👎 remove the distracting subheader | duplicate of FB-008 (same comment submitted twice while testing the website) |

