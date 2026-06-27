## ELI5

Imagine you built a robot that grades how nice a poster looks, all by measuring it —
no eyeballs needed. The robot has lots of little rules. One rule says: "a heading should
be about one-and-a-half times bigger than the normal text." That "one-and-a-half" number
worked well, but until now we couldn't point to a grown-up book that said where it came
from — it felt like we'd just picked it.

Tonight we went and found the source. It turns out "one-and-a-half" is a real, famous step
that designers borrow from **music**: like the gap between two notes that sound good
together (a "perfect fifth"), there's a matching size-jump for text that looks good
together. So our number isn't random — it's a known, trusted choice. We wrote down where
it comes from and tidied our notes. We changed **zero** of the actual grading, so every
poster still gets exactly the same grade as before. We just finally know *why* we picked
that number.

## Broad strokes

The slide-building tool is fully built — all the main work is done. So tonight, like recent
nights, was a "make our claims honest and well-sourced" session rather than new building.

The tool includes an advisory beauty-scorer that judges slides purely from their geometry
and colors (never by looking at a picture). A scorer like that lives or dies by whether its
internal numbers are defensible. We keep a running list of the research and design tradition
behind each number. One number — how much bigger a title should be than the body text — had
its *general idea* sourced last week, but the *exact value* (1.5×) was still just labeled
"our best guess, source not yet confirmed."

Tonight we confirmed it from a primary, publicly-readable design source: 1.5× is the
"perfect fifth," a well-established harmonious size-step that typographers borrow from
musical intervals. That moves our number from "unverified guess" to "a recognized choice
within a documented family of good ratios." We were careful and conservative: the source
offers a *menu* of good ratios (not one mandatory value), so we honestly noted that picking
1.5 specifically is still our judgment — and, crucially, we did **not** change any grading.
The before-and-after scores are identical. We also added the new source to our bibliography
(now 22 verified references) and double-checked that all the auto-generated project files are
still perfectly in sync. The full automated test suite passes. The result: the project's
quality claims got a little more trustworthy, with no risk to anything that already works.
