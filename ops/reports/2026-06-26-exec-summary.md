## ELI5

Our slide tool can give every slide a tidiness-and-beauty score, all by doing math —
it never looks at a picture. One little rule in that math says: "if a slide uses two
main colours, reward them when they sit a nice distance apart on the colour wheel —
about 30 steps apart counts as nice."

Tonight I went back to the famous colour-science paper that this idea came from, opened
its appendix, and copied down the *exact* distances the scientists actually used. It
turns out our "about 30 steps" is comfortably inside the range they describe — so our
rule is in good company — but the number 30 was our own pick, not something they wrote
down. I wrote that honest finding into our notebook and did **not** change the rule,
because changing the math when nobody asked could quietly move everyone's scores. The
tool still works exactly the same, and a known-good slide scored the same before and
after.

## Broad strokes

The slide builder itself is finished — all the building phases are done. So these
sessions are about strengthening the *evidence* behind the beauty-scoring math: making
sure every rule of thumb either traces back to a real published source or is openly
labelled as our own engineering guess. The goal is honesty, not more features.

This session pulled the original colour-harmony research paper and read its appendix to
get the precise numbers the authors used. That let me say something we couldn't say
before: our colour rule's tolerance sits *inside* the published range, so it's
consistent with the science — while also being clear that the specific number we chose
isn't one the paper states. That nuance matters: it's the difference between "we made
this up" and "this is a defensible choice grounded in known research, with the one
remaining guess clearly flagged." I deliberately resisted the temptation to "fix" the
number to match the paper, because that would change scores without anyone asking and
without proof it's better — that kind of tuning is parked until we have real human-rated
examples to test against.

Everything else stayed healthy: every auto-generated file was checked for drift (none),
the full automated test suite passed, and the work is committed and saved. The running
research library holds at 21 verified sources, all confirmed from original documents.
