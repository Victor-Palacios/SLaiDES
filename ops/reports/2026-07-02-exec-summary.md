## ELI5

Imagine a book of slide designs. Someone flipping through it on their phone left little
sticky notes saying "the bottoms of letters like g and y are getting chopped off," "this
tiny grey text is distracting," and "move this number up so the big words sit in the
middle." Tonight I went through those notes and fixed seven of them.

The biggest one was sneaky: on the phone, the tails of letters were being cut off. It
turned out the little boxes that hold each line of text were built exactly as tall as the
text — with no wiggle room — and then squeezed a bit more, so the very bottom of each line
got trimmed. I gave the text the right amount of room so nothing gets clipped anymore, and
I proved it by taking a picture of the "before" (chopped letters) and the "after" (clean
letters). I also added an automatic checker so this exact problem can never sneak back in.

The rest were tidying: I removed a few small extra lines the reviewer found cluttering, and
I nudged a section number up so the title sits nicely centered. Three trickier notes I left
for next time, with clear instructions, rather than rush and break something.

## Broad strokes

This was a short, focused "feedback blitz" session. The operator has been reviewing every
slide layout from their phone and filing quick thumbs-down notes; ten were waiting. I worked
them smallest-risk-first, finishing and saving each one before moving on.

The standout fix addresses a real quality problem in how the review website displayed the
layouts: text was being visually clipped, which made the designs look broken even though the
actual exported slides were fine. Because the operator judges the layouts from that website,
fixing the display faithfully matters. I was able to look at the actual rendered previews
this session (newly authorized), which let me confirm the problem and the fix with my own
eyes — and, importantly, I turned each visual finding into an automatic test so we don't have
to rely on eyeballing it going forward. That "see it, then lock it in with a test" discipline
is how the project keeps its promise of being verifiable without screenshots.

I also made a couple of small design clean-ups the reviewer asked for and improved one layout's
balance. Along the way the new automatic checker surfaced a related, previously-hidden weakness
in another layout; I recorded it and scheduled it rather than expanding tonight's scope. Three
larger requests — including one asking to delete a whole layout — were left clearly documented
for a longer session, because rushing structural changes in a short window is how mistakes
happen. Everything builds cleanly, all tests pass, and the work is saved.
