# Executive summary — 2026-06-25

## ELI5

Imagine we built a robot that helps make slideshows, and it can also give each
slide a "neatness and beauty" grade — all by measuring shapes and numbers, never by
looking at a picture. One of the things it grades is whether the big title on a slide
is clearly bigger than the small writing, so your eyes know what to read first. Our
robot already rewarded that. But until tonight we couldn't point to a real expert book
or study that said "yes, doing this actually helps people." We were just saying "trust
us, it looks right."

Tonight we went and found a proper, trustworthy source — a chapter in a respected
learning-science handbook — that says: when you give people clear signposts (like a
title that stands out), they understand and remember things better. So now our rule has
a real reason behind it, not just our own opinion. We did **not** change how the robot
grades anything — we only wrote down the proper reason. The slides score exactly the
same as before. We were also careful and honest: the *exact* "how much bigger" number we
use is still our own best guess, and we said so plainly instead of pretending a book told
us the precise figure.

## Broad strokes

The slide-builder is feature-complete; nightly sessions now keep it healthy and keep
strengthening the research foundation behind its "is this slide well-designed?" score.
Each part of that score is supposed to trace back to a real, verified piece of published
research. One part — the rule that a slide's title should be clearly larger than its body
text — was the last piece still resting only on our own judgment, with no source attached.

This session closed most of that gap. We searched, found, and verified (from the
publisher's own page) a peer-reviewed chapter on the "signaling principle" from
learning-science research: clear visual signposts that show how material is organized help
people learn. That directly justifies *why* rewarding a strong title-to-body size step is
sound. We added it to our bibliography as our 21st verified source and updated the internal
"which research backs which rule" map so it no longer shows any rule as completely
unsourced.

Two points of discipline are worth calling out. First, we changed **no** scoring behavior:
this was about grounding an existing rule in evidence, not retuning it, and we confirmed a
sample slide's grade was identical before and after. Second, we resisted overclaiming: the
*precise* size ratio we use comes from a typography convention, and although a famous
typography book is the obvious place to confirm it, we could only find that detail in
second-hand summaries tonight — so we honestly recorded it as "still our best guess, source
to confirm later" rather than dressing it up. The full automated test suite passed (325
checks), and the day's work — research notes, the updated map, and the task board — was
committed and pushed.
