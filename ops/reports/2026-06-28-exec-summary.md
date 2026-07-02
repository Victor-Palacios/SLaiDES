## ELI5

Imagine you built a robot that grades how nice a slide looks — is it too crowded with
words, or nicely clear? Tonight I didn't change how the robot grades. Instead I went to
the library to find a real science experiment that proves the robot is grading the right
thing.

I found a good one: scientists put 209 students in a room and showed them three kinds of
slides — none, busy ones full of words, and clean simple ones. The students who saw the
busy, word-stuffed slides actually *remembered less* of what the speaker said out loud,
because their eyes were too busy reading to listen. The clean slides fixed that.

So the robot's rule "fewer words is better" now has a real experiment behind it. But the
exact number the robot uses for "too many words" is still just our best guess — the
experiment said "use as few words as possible," it never named a magic number. I wrote
that down honestly instead of pretending we found one.

## Broad strokes

The slide-builder tool is finished and working — every building phase is done, and all
325 automated checks passed again tonight. With nothing left to build, this was a
"keep-the-research-honest" session: the project maintains a small, carefully-checked
bibliography that explains *why* each grading rule exists, and the goal is for every rule
to point at a real, verified source rather than a hunch.

The one rule that still leaned on weak sourcing was the "how crowded is this slide" score.
Tonight I found and verified a strong, peer-reviewed experiment (published in a respected
education-research journal) that directly tests crowded vs. clean slides on real students.
It confirms the *direction* of our rule — crowding hurts — and even explains the reason:
busy slides steal the audience's attention away from the speaker. I added it to the
bibliography (now 23 verified sources) and updated the supporting documents.

Crucially, I was careful *not* to secretly tweak the grades. The research confirms the
idea, not the precise cutoffs, and changing the cutoffs without a proper labelled dataset
would be guessing dressed up as science. So the scores are byte-for-byte identical to last
night — a well-designed sample slide still scores 89.5, exactly as before. The work was
recorded, committed, and saved, and there's a clear one-line note for what to verify next.
