"""The page number is emitted as an auto-updating slide-number field in PPTX.

slidekit's page number already equals the physical slide position, so a native
<a:fld type="slidenum"> shows the same value AND renumbers live when slides are
moved/added in PowerPoint or Google Slides (a static text run does not). The title
slide, which slidekit skips, must carry no field, and a non-default `start_at` must
set the deck-wide slide-number origin so the field value still matches.
"""
from __future__ import annotations

import re
import zipfile

from slidekit.ir.parse import loads
from slidekit.layout import resolve
from slidekit.emit.pptx_emitter import emit_pptx

_DECK = """
version: 1
page_numbers:
  enabled: true
  start_at: 1
  skip_title_slide: true
slides:
  - component: title-slide
    title: Cover
  - component: bullet-list
    title: Body
    items: [a, b]
  - component: bullet-list
    title: More
    items: [c, d]
"""


def _slide_xml(path, n):
    return zipfile.ZipFile(path).read(f"ppt/slides/slide{n}.xml").decode()


def test_page_number_node_is_marked_as_a_field():
    rd = resolve(loads(_DECK))
    pn = [c for rs in rd.slides for c in rs.chrome
          if c.node_id.startswith("chrome_pagenum")]
    assert pn and all(n.field == "slidenum" for n in pn)


def test_pptx_emits_slidenum_field_not_static_text(tmp_path):
    deck = loads(_DECK)
    out = tmp_path / "d.pptx"
    emit_pptx(deck, resolve(deck), out)
    # Content slides (2, 3) carry a slidenum field with the right initial value.
    for n, val in [(2, "2"), (3, "3")]:
        xml = _slide_xml(out, n)
        m = re.search(r'<a:fld[^>]*type="slidenum"[^>]*>(.*?)</a:fld>', xml, re.S)
        assert m, f"slide {n} has no slidenum field"
        assert f"<a:t>{val}</a:t>" in m.group(0)


def test_skipped_title_slide_has_no_field(tmp_path):
    deck = loads(_DECK)
    out = tmp_path / "d.pptx"
    emit_pptx(deck, resolve(deck), out)
    assert "slidenum" not in _slide_xml(out, 1)


def test_start_at_sets_deck_slide_number_origin(tmp_path):
    deck = loads(_DECK.replace("start_at: 1", "start_at: 5"))
    out = tmp_path / "d.pptx"
    emit_pptx(deck, resolve(deck), out)
    pres = zipfile.ZipFile(out).read("ppt/presentation.xml").decode()
    assert 'firstSlideNum="5"' in pres
    # Physical slide 2 now shows 6 (5 + its 0-based content offset), matching layout.
    m = re.search(r'<a:fld[^>]*type="slidenum"[^>]*>(.*?)</a:fld>', _slide_xml(out, 2), re.S)
    assert m and "<a:t>6</a:t>" in m.group(0)
