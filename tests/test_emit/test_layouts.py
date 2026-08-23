"""Slide-layout structure of the emitted pptx package.

Every other emitter test goes through python-pptx's object model, which is exactly
why the original defect was invisible: the package looked fine object-wise while
every slide pointed at the stock "Blank" layout, so Google Slides' Slide > Edit
theme listed only the 11 Office layouts and none of the slidekit designs. These
tests read the raw OOXML parts and relationships instead.
"""
from __future__ import annotations

import re
import typing
import zipfile
from pathlib import Path

import pytest

from slidekit.emit.prototypes import PROTOTYPES
from slidekit.emit.pptx_emitter import _layout_name, emit_pptx
from slidekit.ir import load
from slidekit.ir.models import Slide
from slidekit.layout import resolve

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"

_LAYOUT_PART_RE = re.compile(r"^ppt/slideLayouts/slideLayout\d+\.xml$")
_STOCK_LAYOUT_COUNT = 11


@pytest.fixture(scope="module")
def emitted(tmp_path_factory) -> zipfile.ZipFile:
    """A five-slide, five-component deck emitted once for the whole module."""
    deck = load(EXAMPLES_DIR / "09_full_deck.yaml")
    out = emit_pptx(deck, resolve(deck), tmp_path_factory.mktemp("pptx") / "d.pptx")
    return zipfile.ZipFile(out)


def _layout_parts(z: zipfile.ZipFile) -> list[str]:
    return [n for n in z.namelist() if _LAYOUT_PART_RE.match(n)]


def _cSld_name(z: zipfile.ZipFile, part: str) -> str:
    xml = z.read(part).decode()
    m = re.search(r"<p:cSld[^>]*\bname=\"([^\"]*)\"", xml)
    return m.group(1) if m else ""


def _layout_for_slide(z: zipfile.ZipFile, one_based: int) -> str:
    rels = z.read(f"ppt/slides/_rels/slide{one_based}.xml.rels").decode()
    return re.search(r"slideLayout\d+\.xml", rels).group(0)


class TestPrototypeCoverage:
    def test_every_component_has_prototype_art(self):
        """A new component must not silently miss its layout."""
        models = typing.get_args(typing.get_args(Slide)[0])
        components = {
            typing.get_args(m.model_fields["component"].annotation)[0] for m in models
        }
        assert components - set(PROTOTYPES) == set(), (
            "components with no prototype — run scripts/build_prototypes.py"
        )


class TestLayoutParts:
    def test_one_layout_per_component_plus_stock(self, emitted):
        assert len(_layout_parts(emitted)) == _STOCK_LAYOUT_COUNT + len(PROTOTYPES)

    def test_each_design_named_exactly_once(self, emitted):
        names = [_cSld_name(emitted, p) for p in _layout_parts(emitted)]
        for component in PROTOTYPES:
            assert names.count(_layout_name(component)) == 1, (
                f"{component}: expected exactly one layout named "
                f"{_layout_name(component)!r}, got {names.count(_layout_name(component))}"
            )

    def test_layout_names_are_unique(self, emitted):
        """Our names must not collide with the stock Office ones."""
        names = [_cSld_name(emitted, p) for p in _layout_parts(emitted)]
        assert len(names) == len(set(names)), "duplicate layout names"

    def test_stock_office_layouts_are_kept(self, emitted):
        names = {_cSld_name(emitted, p) for p in _layout_parts(emitted)}
        assert {"Blank", "Title Slide", "Title and Content"} <= names

    def test_layouts_carry_art(self, emitted):
        """A layout with no shapes would show up empty in the theme editor."""
        by_name = {_cSld_name(emitted, p): p for p in _layout_parts(emitted)}
        for component in PROTOTYPES:
            xml = emitted.read(by_name[_layout_name(component)]).decode()
            assert "<p:sp>" in xml or "<p:pic>" in xml, (
                f"{component}: layout carries no shapes"
            )

    def test_layouts_are_preserved(self, emitted):
        """preserve=1 stops PowerPoint dropping layouts no slide happens to use."""
        for part in _layout_parts(emitted):
            if _cSld_name(emitted, part).startswith("slidekit"):
                assert 'preserve="1"' in emitted.read(part).decode()


class TestMasterRegistration:
    def test_master_lists_every_layout(self, emitted):
        master = emitted.read("ppt/slideMasters/slideMaster1.xml").decode()
        ids = re.findall(r"<p:sldLayoutId\b[^>]*/>", master)
        assert len(ids) == _STOCK_LAYOUT_COUNT + len(PROTOTYPES)

    def test_layout_ids_are_unique(self, emitted):
        master = emitted.read("ppt/slideMasters/slideMaster1.xml").decode()
        ids = re.findall(r'<p:sldLayoutId[^>]*\bid="(\d+)"', master)
        assert len(ids) == len(set(ids))

    def test_every_layout_rid_resolves(self, emitted):
        master = emitted.read("ppt/slideMasters/slideMaster1.xml").decode()
        rels = emitted.read("ppt/slideMasters/_rels/slideMaster1.xml.rels").decode()
        targets = dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', rels))
        for rid in re.findall(r'<p:sldLayoutId[^>]*r:id="([^"]+)"', master):
            assert rid in targets, f"{rid} has no relationship"
            assert "slideLayout" in targets[rid]

    def test_content_types_declare_every_layout(self, emitted):
        ct = emitted.read("[Content_Types].xml").decode()
        for part in _layout_parts(emitted):
            assert "/" + part in ct, f"{part} missing a content-type override"


class TestSlideBinding:
    def test_slide_uses_layout_for_its_component(self, emitted):
        deck = load(EXAMPLES_DIR / "09_full_deck.yaml")
        for i, rs in enumerate(resolve(deck).slides, start=1):
            part = "ppt/slideLayouts/" + _layout_for_slide(emitted, i)
            assert _cSld_name(emitted, part) == _layout_name(rs.component)

    def test_slides_no_longer_share_the_blank_layout(self, emitted):
        """The actual regression: every slide used to point at slideLayout7 (Blank)."""
        deck = load(EXAMPLES_DIR / "09_full_deck.yaml")
        n = len(resolve(deck).slides)
        used = {_layout_for_slide(emitted, i) for i in range(1, n + 1)}
        assert len(used) == n, "distinct components must not share one layout"

    def test_slides_suppress_inherited_layout_graphics(self, emitted):
        """Layout art is for the theme editor; it must not paint onto slides."""
        deck = load(EXAMPLES_DIR / "09_full_deck.yaml")
        for i in range(1, len(resolve(deck).slides) + 1):
            xml = emitted.read(f"ppt/slides/slide{i}.xml").decode()
            assert re.search(r"<p:sld\b[^>]*showMasterSp=\"0\"", xml)


class TestPresentationMetadata:
    def test_slide_size_type_matches_dimensions(self, emitted):
        """The 4:3 default template left a stale type on a 16:9 canvas."""
        xml = emitted.read("ppt/presentation.xml").decode()
        sldSz = re.search(r"<p:sldSz[^>]*/>", xml).group(0)
        assert 'cx="12192000"' in sldSz and 'type="screen16x9"' in sldSz
