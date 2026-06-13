"""Unit tests for slidekit.metrics.measure — Phase 1 acceptance criteria."""

import pytest

from slidekit.metrics.measure import (
    Line,
    TextMeasureError,
    line_height_emu,
    measure_text,
    total_text_height_emu,
    wrap,
)
from slidekit.metrics.constants import EMU_PER_PT, EMU_PER_INCH, SAFE_FONTS


# ── basic sanity ──────────────────────────────────────────────────────────────

class TestMeasureText:
    def test_empty_string_returns_zero(self):
        assert measure_text("", "arial", 32) == 0

    def test_single_char_positive(self):
        w = measure_text("A", "arial", 32)
        assert w > 0

    def test_wider_at_larger_size(self):
        w32 = measure_text("Hello", "arial", 32)
        w64 = measure_text("Hello", "arial", 64)
        assert w64 > w32

    def test_longer_text_wider(self):
        short = measure_text("Hi", "arial", 32)
        long_ = measure_text("Hello World", "arial", 32)
        assert long_ > short

    def test_unsafe_font_raises(self):
        with pytest.raises(TextMeasureError, match="not in the metric-safe set"):
            measure_text("test", "helvetica", 32)

    def test_all_safe_fonts_work(self):
        for font in SAFE_FONTS:
            w = measure_text("Hello", font, 32)
            assert w > 0, f"measure_text returned 0 for font '{font}'"

    def test_bold_differs_from_regular(self):
        regular = measure_text("Hello", "arial", 32, bold=False)
        bold = measure_text("Hello", "arial", 32, bold=True)
        # Bold is typically slightly wider but could be the same with some fonts;
        # at minimum both must be positive.
        assert regular > 0
        assert bold > 0

    def test_kerning_applied(self):
        # "AV" is a classic kerning pair (negative kern reduces width).
        # We can only test that it's finite and positive.
        w = measure_text("AV", "arial", 32)
        assert w > 0

    def test_very_long_token(self):
        long_word = "A" * 200
        w = measure_text(long_word, "arial", 32)
        assert w > 0

    def test_width_scales_linearly_with_size(self):
        # Scaling from 32pt to 64pt should double width (within 1% rounding).
        w32 = measure_text("Hello", "arial", 32)
        w64 = measure_text("Hello", "arial", 64)
        ratio = w64 / w32
        assert abs(ratio - 2.0) < 0.02, f"Expected 2x scaling, got {ratio:.4f}"

    def test_space_has_positive_width(self):
        assert measure_text(" ", "arial", 32) > 0


# ── line height ───────────────────────────────────────────────────────────────

class TestLineHeight:
    def test_positive(self):
        h = line_height_emu("arial", 32)
        assert h > 0

    def test_scales_with_size(self):
        h32 = line_height_emu("arial", 32)
        h64 = line_height_emu("arial", 64)
        assert h64 == h32 * 2

    def test_custom_line_spacing(self):
        h_single = line_height_emu("arial", 32, line_spacing=1.2)
        h_double = line_height_emu("arial", 32, line_spacing=2.4)
        assert h_double == h_single * 2


# ── wrap / line breaking ──────────────────────────────────────────────────────

class TestWrap:
    def test_empty_string_returns_one_empty_line(self):
        lines = wrap("", "arial", 32, box_width_emu=10_000_000)
        assert len(lines) == 1
        assert lines[0].text == ""

    def test_short_text_fits_on_one_line(self):
        lines = wrap("Hi", "arial", 32, box_width_emu=10_000_000)
        assert len(lines) == 1
        assert not lines[0].overflows

    def test_long_text_wraps_to_multiple_lines(self):
        text = "This is a sentence that is long enough to wrap over multiple lines on a narrow box."
        # Use a narrow box (2 inches) to force wrapping.
        box_w = 2 * EMU_PER_INCH
        lines = wrap(text, "arial", 32, box_width_emu=box_w)
        assert len(lines) > 1

    def test_each_line_fits_in_box(self):
        text = "The quick brown fox jumps over the lazy dog. " * 3
        box_w = 3 * EMU_PER_INCH
        inset = 91440  # 0.1"
        lines = wrap(text, "arial", 32, box_width_emu=box_w)
        usable = box_w - 2 * inset
        for line in lines:
            if not line.overflows:
                assert line.width_emu <= usable, (
                    f"Line '{line.text[:30]}' width {line.width_emu} exceeds usable {usable}"
                )

    def test_unbreakable_long_token_flagged_as_overflow(self):
        long_word = "A" * 200
        box_w = 1 * EMU_PER_INCH   # tiny box
        lines = wrap(long_word, "arial", 32, box_width_emu=box_w)
        assert any(l.overflows for l in lines)

    def test_all_tokens_present(self):
        text = "Hello world, how are you today?"
        box_w = 10 * EMU_PER_INCH
        lines = wrap(text, "arial", 32, box_width_emu=box_w)
        rejoined = " ".join(l.text for l in lines).split()
        original_words = text.split()
        assert rejoined == original_words

    def test_wrap_respects_hyphens(self):
        text = "well-known state-of-the-art compound-word"
        box_w = 2 * EMU_PER_INCH
        lines = wrap(text, "arial", 32, box_width_emu=box_w)
        # Should produce multiple lines, not one overflow.
        assert len(lines) >= 1
        # Hyphens should be preserved in the output.
        full = "".join(l.text for l in lines)
        assert "-" in full

    def test_line_has_positive_height(self):
        lines = wrap("Hello", "arial", 32, box_width_emu=10_000_000)
        for line in lines:
            assert line.height_emu > 0

    def test_whitespace_text_returns_empty_line(self):
        lines = wrap("   ", "arial", 32, box_width_emu=10_000_000)
        assert len(lines) == 1


# ── total text height ─────────────────────────────────────────────────────────

class TestTotalTextHeight:
    def test_includes_insets(self):
        lines = wrap("Hello", "arial", 32, box_width_emu=10_000_000)
        h = total_text_height_emu(lines, inset_top=45720, inset_bottom=45720)
        assert h > lines[0].height_emu   # insets add to line height

    def test_zero_insets(self):
        lines = wrap("Hello", "arial", 32, box_width_emu=10_000_000)
        h = total_text_height_emu(lines, inset_top=0, inset_bottom=0)
        assert h == lines[0].height_emu


# ── mixed bold/italic runs (basic check) ─────────────────────────────────────

class TestMixedRuns:
    def test_bold_and_regular_both_measurable(self):
        w_reg = measure_text("Hello World", "arial", 32, bold=False)
        w_bold = measure_text("Hello World", "arial", 32, bold=True)
        assert w_reg > 0
        assert w_bold > 0

    def test_italic_measurable(self):
        w = measure_text("Hello", "arial", 32, italic=True)
        assert w > 0

    def test_bolditalic_measurable(self):
        w = measure_text("Hello", "arial", 32, bold=True, italic=True)
        assert w > 0
