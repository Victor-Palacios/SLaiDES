"""Render-and-check harness: .pptx -> pdf -> png -> pixel heuristics.

Pipeline per deck:

    deck.yaml --(load/resolve/lint/emit)--> deck.pptx
              --(soffice --headless --convert-to pdf)--> deck.pdf
              --(pdftoppm -png -r DPI)--> slide-N.png
              --(pixel heuristics vs ResolvedDeck)--> pass / fail

Two heuristics, both cheap and deterministic:

1. ``ink_outside_rects`` — every "ink" pixel (any pixel differing from the slide's
   surface colour) must fall inside the slack-dilated union of the resolved node
   rects. A renderer that overflows a text box past where our math said it would
   shows up as ink outside the union. This is the core drift signal.

2. ``ink_in_margin`` — no ink in the 0.5" edge band, except inside the reserved
   page-number chrome corner. Catches content drifting into the margin zone.

Both are expressed as *fractions* with conservative thresholds: the harness must
not cry wolf on decks the linter already passed (the example decks), but must still
catch gross overflow (text running well past its box, or off the slide).

Pillow only — no numpy. All per-pixel work is done with C-level ``ImageChops`` /
``ImageDraw`` ops so a 2000x1125 slide checks in milliseconds.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image, ImageChops, ImageDraw

from slidekit.metrics.constants import (
    EMU_PER_INCH,
    MARGIN_MIN_EMU,
)

# --- tuning constants -------------------------------------------------------
# These are the harness's only knobs. They are deliberately generous: the harness
# is a drift detector, not a pixel-perfect oracle. See module docstring.

DEFAULT_DPI = 150

# A pixel counts as "ink" if any RGB channel differs from the surface colour by
# more than this (0-255). Absorbs JPEG-ish AA fuzz; well below any real glyph.
INK_CHANNEL_THRESHOLD = 40

# Each resolved rect is dilated by this many inches before forming the "allowed"
# union. Absorbs anti-alias halos and small sub-pixel renderer drift while still
# flagging gross overflow (text spilling an inch past its computed box).
RECT_TOLERANCE_IN = 0.08

# Fail the slide if more than this fraction of ink pixels land outside the union.
MAX_STRAY_INK_FRACTION = 0.01  # 1%

# Fail the slide if margin-band ink exceeds this fraction of total pixels.
MAX_MARGIN_INK_FRACTION = 0.001  # 0.1%


@dataclass
class VerifyConfig:
    """Knobs for a verification run (defaults are the tuned CI values)."""

    dpi: int = DEFAULT_DPI
    ink_channel_threshold: int = INK_CHANNEL_THRESHOLD
    rect_tolerance_in: float = RECT_TOLERANCE_IN
    max_stray_ink_fraction: float = MAX_STRAY_INK_FRACTION
    max_margin_ink_fraction: float = MAX_MARGIN_INK_FRACTION


@dataclass
class SlideVerifyResult:
    """Per-slide heuristic outcome."""

    slide_index: int
    png_path: str
    img_w: int
    img_h: int
    ink_pixels: int
    stray_ink_pixels: int
    stray_ink_fraction: float
    margin_ink_pixels: int
    margin_ink_fraction: float
    passed: bool
    failures: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "slide_index": self.slide_index,
            "png": self.png_path,
            "img_w": self.img_w,
            "img_h": self.img_h,
            "ink_pixels": self.ink_pixels,
            "stray_ink_pixels": self.stray_ink_pixels,
            "stray_ink_fraction": round(self.stray_ink_fraction, 6),
            "margin_ink_pixels": self.margin_ink_pixels,
            "margin_ink_fraction": round(self.margin_ink_fraction, 6),
            "passed": self.passed,
            "failures": self.failures,
        }


@dataclass
class DeckVerifyResult:
    """Whole-deck outcome: passes only if every slide passes."""

    deck: str
    passed: bool
    slides: list[SlideVerifyResult] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "deck": self.deck,
            "passed": self.passed,
            "error": self.error,
            "slides": [s.to_dict() for s in self.slides],
        }


class HarnessError(RuntimeError):
    """Raised when the external render pipeline fails."""


# --- external tool availability ---------------------------------------------

def _soffice_bin() -> Optional[str]:
    return shutil.which("soffice") or shutil.which("libreoffice")


def tools_available() -> tuple[bool, str]:
    """Return (available, reason). reason is empty when available."""
    missing = []
    if _soffice_bin() is None:
        missing.append("soffice/libreoffice")
    if shutil.which("pdftoppm") is None:
        missing.append("pdftoppm")
    if missing:
        return False, "missing external tools: " + ", ".join(missing)
    return True, ""


# --- render pipeline --------------------------------------------------------

def render_pptx_to_pngs(pptx_path: Path, out_dir: Path, dpi: int = DEFAULT_DPI) -> list[Path]:
    """Render ``pptx_path`` to one PNG per slide via LibreOffice + pdftoppm.

    Returns the PNG paths in slide order. Raises HarnessError on tool failure.
    """
    soffice = _soffice_bin()
    if soffice is None or shutil.which("pdftoppm") is None:
        raise HarnessError("render tools unavailable (need soffice + pdftoppm)")

    pptx_path = Path(pptx_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. pptx -> pdf. LibreOffice writes <stem>.pdf into the --outdir. A dedicated
    #    per-call user profile dir avoids the shared-profile lock that makes
    #    concurrent/headless soffice invocations flaky.
    with tempfile.TemporaryDirectory() as profile:
        proc = subprocess.run(
            [
                soffice,
                "--headless",
                "--norestore",
                f"-env:UserInstallation=file://{profile}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out_dir),
                str(pptx_path),
            ],
            capture_output=True,
            text=True,
            timeout=180,
        )
    pdf_path = out_dir / (pptx_path.stem + ".pdf")
    if proc.returncode != 0 or not pdf_path.exists():
        raise HarnessError(
            f"soffice pdf conversion failed (rc={proc.returncode}): "
            f"{proc.stderr.strip() or proc.stdout.strip()}"
        )

    # 2. pdf -> png per page. pdftoppm writes <prefix>-N.png, zero-padded to the
    #    page-count width.
    prefix = out_dir / pptx_path.stem
    proc = subprocess.run(
        ["pdftoppm", "-png", "-r", str(dpi), str(pdf_path), str(prefix)],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if proc.returncode != 0:
        raise HarnessError(
            f"pdftoppm failed (rc={proc.returncode}): {proc.stderr.strip()}"
        )

    pngs = sorted(
        out_dir.glob(pptx_path.stem + "-*.png"),
        key=lambda p: int(p.stem.rsplit("-", 1)[1]),
    )
    if not pngs:
        raise HarnessError("pdftoppm produced no PNGs")
    return pngs


# --- pixel heuristics -------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _collect_rects(nodes) -> list:
    """Flatten every node rect (recursively) into a list of Rect."""
    out = []
    for n in nodes:
        out.append(n.rect)
        if n.children:
            out.extend(_collect_rects(n.children))
    return out


def _ink_mask(img: Image.Image, surface_rgb: tuple[int, int, int], threshold: int) -> Image.Image:
    """Mode-'1' mask: True where the pixel differs from surface on any channel."""
    surf = Image.new("RGB", img.size, surface_rgb)
    diff = ImageChops.difference(img, surf)
    r, g, b = diff.split()
    # per-pixel max across channels, so a strong single-channel diff isn't diluted
    chan_max = ImageChops.lighter(ImageChops.lighter(r, g), b)
    return chan_max.point(lambda v: 255 if v > threshold else 0).convert("1")


def _count_on(mask: Image.Image) -> int:
    """Number of set pixels in a mode-'1' mask (C-level histogram)."""
    return mask.histogram()[-1]


def check_slide(
    png_path: Path,
    resolved_slide,
    surface_rgb: tuple[int, int, int],
    cfg: VerifyConfig,
) -> SlideVerifyResult:
    """Run both pixel heuristics for one rendered slide against its geometry."""
    img = Image.open(png_path).convert("RGB")
    W, H = img.size
    canvas_w = resolved_slide.canvas_w
    canvas_h = resolved_slide.canvas_h

    # Scale is derived from the actual rendered size, so any DPI/page-size rounding
    # self-corrects (px-per-emu on each axis independently).
    sx = W / canvas_w
    sy = H / canvas_h
    tol_x = cfg.rect_tolerance_in * EMU_PER_INCH * sx
    tol_y = cfg.rect_tolerance_in * EMU_PER_INCH * sy

    def to_px(rect, tol_px_x, tol_px_y):
        x0 = int(rect.x * sx - tol_px_x)
        y0 = int(rect.y * sy - tol_px_y)
        x1 = int(rect.right() * sx + tol_px_x)
        y1 = int(rect.bottom() * sy + tol_px_y)
        return max(0, x0), max(0, y0), min(W - 1, x1), min(H - 1, y1)

    ink = _ink_mask(img, surface_rgb, cfg.ink_channel_threshold)
    ink_count = _count_on(ink)

    # Allowed region: slack-dilated union of every resolved rect (content + chrome).
    all_nodes = resolved_slide.nodes + resolved_slide.chrome
    allowed = Image.new("1", (W, H), 0)
    adraw = ImageDraw.Draw(allowed)
    for rect in _collect_rects(all_nodes):
        x0, y0, x1, y1 = to_px(rect, tol_x, tol_y)
        if x1 >= x0 and y1 >= y0:
            adraw.rectangle([x0, y0, x1, y1], fill=1)

    not_allowed = ImageChops.invert(allowed.convert("L")).convert("1")
    stray = ImageChops.logical_and(ink, not_allowed)
    stray_count = _count_on(stray)
    stray_frac = stray_count / ink_count if ink_count else 0.0

    # Margin band: outer MARGIN_MIN_EMU on every edge, minus chrome rects (the one
    # element allowed to sit in the margin).
    mx = int(MARGIN_MIN_EMU * sx)
    my = int(MARGIN_MIN_EMU * sy)
    margin = Image.new("1", (W, H), 1)
    mdraw = ImageDraw.Draw(margin)
    mdraw.rectangle([mx, my, W - 1 - mx, H - 1 - my], fill=0)  # clear inner area
    for rect in _collect_rects(resolved_slide.chrome):
        x0, y0, x1, y1 = to_px(rect, tol_x, tol_y)
        if x1 >= x0 and y1 >= y0:
            mdraw.rectangle([x0, y0, x1, y1], fill=0)
    margin_ink = ImageChops.logical_and(ink, margin)
    margin_count = _count_on(margin_ink)
    margin_frac = margin_count / (W * H)

    failures = []
    if stray_frac > cfg.max_stray_ink_fraction:
        failures.append(
            f"ink_outside_rects: {stray_frac:.3%} of ink outside computed rects "
            f"(>{cfg.max_stray_ink_fraction:.3%})"
        )
    if margin_frac > cfg.max_margin_ink_fraction:
        failures.append(
            f"ink_in_margin: {margin_frac:.3%} of slide is ink in the 0.5\" margin "
            f"(>{cfg.max_margin_ink_fraction:.3%})"
        )

    return SlideVerifyResult(
        slide_index=resolved_slide.slide_index,
        png_path=str(png_path),
        img_w=W,
        img_h=H,
        ink_pixels=ink_count,
        stray_ink_pixels=stray_count,
        stray_ink_fraction=stray_frac,
        margin_ink_pixels=margin_count,
        margin_ink_fraction=margin_frac,
        passed=not failures,
        failures=failures,
    )


# --- top-level entry point --------------------------------------------------

def verify_deck_yaml(
    deck_yaml: Path,
    work_dir: Optional[Path] = None,
    cfg: Optional[VerifyConfig] = None,
) -> DeckVerifyResult:
    """Full pipeline for one deck YAML: build, render, run heuristics.

    Does NOT raise on lint errors or render failure — captures them in the result's
    ``error`` field so a CI loop can report every deck. Raises only on programmer
    error (bad path types).
    """
    from slidekit.ir import load
    from slidekit.layout import resolve
    from slidekit.emit.pptx_emitter import emit_pptx

    cfg = cfg or VerifyConfig()
    deck_yaml = Path(deck_yaml)
    result = DeckVerifyResult(deck=str(deck_yaml), passed=False)

    cleanup = None
    if work_dir is None:
        cleanup = tempfile.TemporaryDirectory()
        work_dir = Path(cleanup.name)
    else:
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)

    try:
        deck = load(deck_yaml)
        rd = resolve(deck)
        surface_rgb = _hex_to_rgb(deck.theme.palette.surface)

        pptx_path = work_dir / (deck_yaml.stem + ".pptx")
        emit_pptx(deck, rd, pptx_path)

        pngs = render_pptx_to_pngs(pptx_path, work_dir, dpi=cfg.dpi)
        if len(pngs) != len(rd.slides):
            result.error = (
                f"render produced {len(pngs)} png(s) but deck has {len(rd.slides)} slide(s)"
            )
            return result

        for png, rs in zip(pngs, rd.slides):
            result.slides.append(check_slide(png, rs, surface_rgb, cfg))

        result.passed = all(s.passed for s in result.slides)
    except Exception as exc:  # noqa: BLE001 — capture for CI reporting
        result.error = f"{type(exc).__name__}: {exc}"
        result.passed = False
    finally:
        if cleanup is not None:
            cleanup.cleanup()

    return result
