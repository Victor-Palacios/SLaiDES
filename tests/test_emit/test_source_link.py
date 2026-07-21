"""Tests for the per-slide `source` citation — a clickable "Source" link rendered
in the bottom-right chrome, next to the page number.

Covers the full path: IR validation → layout chrome node (position + href) →
lint-cleanliness → hyperlink embedded by each of the three emitters.
"""
from __future__ import annotations

import zipfile

import pytest

from slidekit.ir.parse import loads
from slidekit.layout import resolve
from slidekit.lint.checks import lint, has_errors
from slidekit.emit.pptx_emitter import emit_pptx
from slidekit.emit.pdf_emitter import emit_pdf
from slidekit.emit.html_preview import emit_html

URL = "https://code.claude.com/docs/en/mcp"

_WITH_SOURCE = f"""
version: 1
slides:
  - component: definition
    term: "MCP"
    definition: "An open standard for connecting AI tools to external data."
    source: "{URL}"
  - component: title-slide
    title: "No source here"
"""


def _resolve(yaml_text: str):
    deck = loads(yaml_text)
    return deck, resolve(deck)


def _source_nodes(rs):
    return [c for c in rs.chrome if c.href]


# ── IR validation ──────────────────────────────────────────────────────────

def test_source_is_optional():
    _, rd = _resolve(
        "version: 1\nslides:\n  - component: title-slide\n    title: X\n"
    )
    assert _source_nodes(rd.slides[0]) == []


def test_source_accepts_https():
    deck = loads(_WITH_SOURCE)
    assert deck.slides[0].source == URL


@pytest.mark.parametrize("bad", ["ftp://x", "mailto:a@b.c", "just-text", "/docs/x"])
def test_source_rejects_non_http_urls(bad):
    with pytest.raises(ValueError, match="http"):
        loads(
            f'version: 1\nslides:\n  - component: title-slide\n    title: X\n    source: "{bad}"\n'
        )


# ── layout ───────────────────────────────────────────────────────────────────

def test_source_produces_chrome_node_with_href():
    _, rd = _resolve(_WITH_SOURCE)
    nodes = _source_nodes(rd.slides[0])
    assert len(nodes) == 1
    n = nodes[0]
    assert n.href == URL
    assert n.text_content == "Source"
    assert n.is_chrome is True


def test_source_absent_when_not_set():
    _, rd = _resolve(_WITH_SOURCE)
    # Second slide (title-slide) has no source.
    assert _source_nodes(rd.slides[1]) == []


def test_source_sits_left_of_page_number():
    _, rd = _resolve(_WITH_SOURCE)
    rs = rd.slides[0]
    pagenum = [c for c in rs.chrome if c.node_id.startswith("chrome_pagenum")][0]
    src = _source_nodes(rs)[0]
    # Source's right edge is left of the page-number box, on the same baseline.
    assert src.rect.right() <= pagenum.rect.x
    assert src.rect.y == pagenum.rect.y


def test_source_does_not_break_lint():
    deck, rd = _resolve(_WITH_SOURCE)
    assert not has_errors(lint(deck, rd))


# ── emitters embed the hyperlink ──────────────────────────────────────────────

def test_pptx_embeds_hyperlink(tmp_path):
    deck, rd = _resolve(_WITH_SOURCE)
    out = tmp_path / "deck.pptx"
    emit_pptx(deck, rd, out)
    z = zipfile.ZipFile(out)
    rels = z.read("ppt/slides/_rels/slide1.xml.rels").decode()
    assert URL in rels
    assert "hlinkClick" in z.read("ppt/slides/slide1.xml").decode()


def test_pdf_embeds_hyperlink(tmp_path):
    deck, rd = _resolve(_WITH_SOURCE)
    out = tmp_path / "deck.pdf"
    emit_pdf(deck, rd, out)
    data = out.read_bytes()
    assert b"/URI" in data
    assert b"code.claude.com" in data


def test_html_embeds_anchor(tmp_path):
    deck, rd = _resolve(_WITH_SOURCE)
    out = tmp_path / "deck.html"
    emit_html(deck, rd, out)
    html = out.read_text()
    assert f'href="{URL}"' in html
    assert ">Source</a>" in html
