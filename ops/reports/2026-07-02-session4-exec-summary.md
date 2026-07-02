## ELI5

Imagine a poster split into four boxes, and in each box you write a little list.
The lists were being written in letters so big that each line of text was actually
taller than the space the box thought it had. On screen it still looked okay because
the words leaned into the empty gap between them — but the "measurements" the tool
kept for each box were fibbing about how much room the words really needed.

Tonight we made the words in those four boxes a little smaller — the right size for a
tidy grid — so now each line genuinely fits in its box, with room to spare. Nothing
was thrown away; the headings stay big and bold so you can still tell them apart at a
glance. And we added an automatic ruler-check so if this ever happens again, the
computer catches it by itself, without a person needing to squint at the picture.

## Broad strokes

This was a short, focused maintenance session in the middle of a run of quick
two-hour sessions. Every piece of feedback the reviewer had sent in from their phone
had already been handled in earlier sessions, so the list of requests was empty.

That left one leftover item the tool itself had flagged — not a complaint from a
person, but a self-check that noticed the four-box "SWOT" layout was recording its
measurements dishonestly. It had been put off twice before because a quick patch
wasn't safe; it needed a real, considered fix. This session took it on properly: the
list text in that layout now uses a slightly smaller, grid-appropriate size, so every
line honestly fits and the whole thing stays neat and readable.

The important part is the safety net. Rather than just eyeballing the result and
calling it done, we wired the fix into an automatic check that will flag this whole
family of problems in the future — so the quality holds up on its own. All the
project's tests pass, the example gallery was rebuilt, and the work is saved and
pushed. The build is healthy and nothing is left half-finished.
