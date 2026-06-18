# Executive summary — 2026-06-18

## ELI5

Imagine a robot that builds tidy slideshows. It already has a strict "inspector" that
refuses to ship a slide if something is actually broken — words spilling off the edge,
two boxes sitting on top of each other. Tonight we taught the robot a gentler "coach."

The coach doesn't stop anything. It just looks at a finished slide and says helpful
things like "this slide feels lopsided" or "this one looks a bit empty — maybe add a
splash of colour," and gives a friendly tip on how to fix it. We were careful: the
coach only speaks up when something is genuinely off, not for every little thing. And
the coach can never block a slideshow from being made — only the strict inspector can
do that. If a team really wants a quality bar, they can switch on an optional "must
score at least this high" setting, but it's off unless you ask for it.

We also spent time in the library, finding three more trustworthy books about the
*maths of balance* — how to measure whether a slide looks evenly weighted, like a
see-saw that isn't tipping. We double-checked each book is real before adding it to our
shelf. We're now at 18 good books out of a goal of about 20.

## Broad strokes

This session continued the "computational aesthetics" work: turning vague ideas about
"looking good" into precise numbers a computer can calculate without ever needing to
look at a picture — purely from the blueprint of where things sit on the slide.

The main deliverable was an **advisory feedback layer**. The tool can now produce a set
of gentle, clearly-labelled warnings about a slide's design (balance, crowding,
alignment, colour use, and so on), each paired with a concrete suggestion. Crucially,
this advice is *advisory only* — it never prevents a slideshow from being produced,
keeping a clean separation between hard rules (enforced) and matters of taste (suggested).
Teams who want a stricter quality gate in their automated pipelines can opt into a
minimum-score threshold, but nothing changes for anyone who doesn't ask for it. The
thresholds that decide when a warning fires were calibrated against the project's own
40-slide example library so the advice is meaningful, not noisy. Everything is tested
and produces identical results every run.

Alongside the build work, the project keeps a small, carefully-verified research library
on how design quality can be measured mathematically. Tonight it grew by three entries,
all focused on *visual balance* — a cluster that strengthens the foundation under one of
the tool's existing quality measures. Each was confirmed against authoritative records
before being added. The research notes a promising future improvement (a more physics-like
"see-saw" model of balance) but deliberately did not rush it in — it's logged for a later
session. The work was committed and saved in two clean steps, the full automated test
suite passes, and tomorrow's clear next step is recorded.
