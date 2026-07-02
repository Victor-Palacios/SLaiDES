# Executive summary — 2026-06-20

## ELI5

Imagine a teacher grading a poster. The old way added up scores for neatness,
spacing, colours and so on, then took the average — so a poster could still get a
good grade even if one thing was really bad, because the good parts pulled the
average up. Tonight we taught the grader a second, stricter way of adding up the
scores: if even one thing is really bad, the whole grade drops a lot. You can pick
which grading style to use; the gentle average is still the normal one, and the new
strict style is there when you want to make sure no single big mistake slips through.

## Broad strokes

The project is a tool that builds slide decks by maths instead of by eye, and it has
a separate "beauty meter" that gives each deck a score out of 100 from its layout —
all without ever drawing a picture. Until now, that meter blended its nine quality
measures together by simple averaging.

This session added a second, well-known way of blending those measures (named after a
1970s quality-engineering method) where a single serious flaw can't hide behind
otherwise good marks — it drags the whole score down. It's an optional setting: the
familiar averaging stays the default, so all the existing scores and comparisons are
unchanged, and you switch on the stricter mode only when you want it. Importantly, a
deck that's good across the board gets the exact same score either way; the two modes
only differ when something is genuinely lopsided.

This was a small, self-contained improvement that had been written up as a planned
idea for a while and is now actually built and tested, with the documentation updated
to match. With it done, essentially everything on the to-do list is finished except
one task that's deliberately on hold because it needs a batch of human ratings we
don't yet have. The work was checked by the full automated test set (everything
passing) and saved to the project's shared history.
