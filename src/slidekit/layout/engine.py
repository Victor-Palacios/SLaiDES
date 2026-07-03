"""Two-pass flex layout engine.

Converts a DeckIR into a ResolvedDeck where every node has an absolute
EMU rect and every text node has its line boxes.

Pass 1 (measure): compute intrinsic/minimum sizes bottom-up.
Pass 2 (assign):  distribute available space top-down and record rects.
"""

from __future__ import annotations

import itertools
import re
from dataclasses import dataclass, field
from typing import Optional

from slidekit.ir.models import (
    AgendaSlide,
    TwoPanelListSlide,
    BigNumberSlide,
    BulletListSlide,
    CardGridSlide,
    ChartWithInsightSlide,
    CodeSlide,
    ComparisonColumnsSlide,
    ComparisonMatrixSlide,
    DeckIR,
    DefinitionSlide,
    FeatureListSlide,
    FunnelSlide,
    IconTextRowsSlide,
    ImageHalfBleedSlide,
    ImageFullBleedSlide,
    ImageGridSlide,
    KpiGridSlide,
    LogoWallSlide,
    Matrix2x2Slide,
    MetricComparisonSlide,
    NumberedStepsSlide,
    ProcessStepsSlide,
    PullQuoteSlide,
    PyramidSlide,
    QuestionSlide,
    QuoteOpenerSlide,
    RoadmapSlide,
    SectionDividerSlide,
    StatCalloutSlide,
    StatementSlide,
    SwotSlide,
    TableSlide,
    TeamGridSlide,
    ThisVsThatSlide,
    TimelineSlide,
    TitleSlide,
    TextSlot,
    ImageSlot,
    ChartSlot,
    IconSlot,
    SpacerSlot,
)
from slidekit.layout.models import Rect, ResolvedDeck, ResolvedNode, ResolvedSlide
from slidekit.metrics.constants import (
    BODY_FONT_FLOOR_PT,
    EMU_PER_INCH,
    EMU_PER_PT,
    GAP_MIN_EMU,
    INSET_BOTTOM_EMU,
    INSET_LEFT_EMU,
    INSET_RIGHT_EMU,
    INSET_TOP_EMU,
    LINE_SPACING_SINGLE,
    MARGIN_MIN_EMU,
    PAGE_NUMBER_PT,
    SLIDE_16_9_H,
    SLIDE_16_9_W,
    SLIDE_4_3_H,
    SLIDE_4_3_W,
)
from slidekit.metrics.measure import Line, line_height_emu, measure_text, total_text_height_emu, wrap

# Unique ID counter for nodes.
_counter = itertools.count(1)


def _nid(prefix: str = "node") -> str:
    return f"{prefix}_{next(_counter)}"


# ── public entry point ────────────────────────────────────────────────────────


def resolve(deck: DeckIR, aspect: str = "16:9") -> ResolvedDeck:
    """Resolve a DeckIR into a ResolvedDeck with absolute EMU geometry."""
    if aspect == "4:3":
        canvas_w, canvas_h = SLIDE_4_3_W, SLIDE_4_3_H
    else:
        canvas_w, canvas_h = SLIDE_16_9_W, SLIDE_16_9_H

    resolved_slides: list[ResolvedSlide] = []
    page_num_counter = deck.page_numbers.start_at - 1

    for idx, slide in enumerate(deck.slides):
        is_title = slide.component == "title-slide"
        page_num_counter += 1
        page_num = page_num_counter if deck.page_numbers.enabled else None
        # skip_title_slide hides the number on the first title-slide (cover) only.
        if idx == 0 and is_title and deck.page_numbers.skip_title_slide:
            page_num = None

        rs = _resolve_slide(
            slide=slide,
            slide_index=idx,
            page_num=page_num,
            deck=deck,
            canvas_w=canvas_w,
            canvas_h=canvas_h,
        )
        resolved_slides.append(rs)

    return ResolvedDeck(slides=resolved_slides)


# ── slide resolver ────────────────────────────────────────────────────────────


def _resolve_slide(
    slide,
    slide_index: int,
    page_num: Optional[int],
    deck: DeckIR,
    canvas_w: int,
    canvas_h: int,
) -> ResolvedSlide:
    theme = deck.theme
    font = theme.font
    ts = theme.type_scale
    palette = theme.palette

    # Content area: slide canvas minus the minimum margins on all sides.
    cx = MARGIN_MIN_EMU
    cy = MARGIN_MIN_EMU
    cw = canvas_w - 2 * MARGIN_MIN_EMU
    ch = canvas_h - 2 * MARGIN_MIN_EMU

    # Reserve bottom-right corner for page numbers (chrome).
    pn_box_w = int(1.5 * EMU_PER_INCH)
    pn_box_h = int(0.4 * EMU_PER_INCH)
    pn_x = canvas_w - MARGIN_MIN_EMU - pn_box_w
    pn_y = canvas_h - MARGIN_MIN_EMU - pn_box_h
    # Shrink content area height to avoid chrome overlap.
    ch_with_pn = ch - pn_box_h - GAP_MIN_EMU

    nodes: list[ResolvedNode] = []
    comp = slide.component

    if comp == "title-slide":
        nodes = _layout_title_slide(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "icon-text-rows":
        nodes = _layout_icon_text_rows(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "stat-callout":
        nodes = _layout_stat_callout(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "comparison-columns":
        nodes = _layout_comparison_columns(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "timeline":
        nodes = _layout_timeline(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "image-half-bleed":
        nodes = _layout_image_half_bleed(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "card-grid":
        nodes = _layout_card_grid(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    # Emphasis-stack hero layouts center a short text block: center it on the FULL content
    # height (the optical canvas midline), NOT the page-number-reduced height — otherwise
    # the block sits ~25px high (top-heavy, hurting balance). These blocks are short and
    # never reach the bottom-right page-number corner; the linter still guards overlap.
    elif comp == "section-divider":
        nodes = _layout_section_divider(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "agenda":
        nodes = _layout_agenda(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "quote-opener":
        nodes = _layout_quote_opener(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "big-number":
        nodes = _layout_big_number(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "pull-quote":
        nodes = _layout_pull_quote(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "statement":
        nodes = _layout_statement(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "definition":
        nodes = _layout_definition(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "question":
        nodes = _layout_question(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "bullet-list":
        nodes = _layout_bullet_list(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "feature-list":
        nodes = _layout_feature_list(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "code":
        # Full canvas height (not ch_with_pn): the dark panel bleeds edge-to-edge.
        nodes = _layout_code(slide, cx, cy, cw, ch, font, ts, palette)
    elif comp == "numbered-steps":
        nodes = _layout_numbered_steps(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "two-panel-list":
        nodes = _layout_two_panel_list(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "this-vs-that":
        nodes = _layout_this_vs_that(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "kpi-grid":
        nodes = _layout_kpi_grid(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "chart-with-insight":
        nodes = _layout_chart_with_insight(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "table-slide":
        nodes = _layout_table_slide(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "metric-comparison":
        nodes = _layout_metric_comparison(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "process-steps":
        nodes = _layout_process_steps(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "roadmap":
        nodes = _layout_roadmap(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "funnel":
        nodes = _layout_funnel(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "pyramid":
        nodes = _layout_pyramid(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "matrix-2x2":
        nodes = _layout_matrix_2x2(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "swot":
        nodes = _layout_swot(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "comparison-matrix":
        nodes = _layout_comparison_matrix(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "team-grid":
        nodes = _layout_team_grid(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "image-full-bleed":
        nodes = _layout_image_full_bleed(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "image-grid":
        nodes = _layout_image_grid(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "logo-wall":
        nodes = _layout_logo_wall(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    else:
        nodes = []

    # Chrome: page number box (laid out last, always bottom-right).
    chrome: list[ResolvedNode] = []
    if page_num is not None and deck.page_numbers.enabled:
        pn_node = _make_text_node(
            node_id=_nid("chrome_pagenum"),
            text=str(page_num),
            font=font,
            size_pt=PAGE_NUMBER_PT,
            bold=False,
            italic=False,
            rect=Rect(pn_x, pn_y, pn_box_w, pn_box_h),
            is_chrome=True,
        )
        chrome.append(pn_node)

    return ResolvedSlide(
        slide_index=slide_index,
        page_number=page_num,
        component=comp,
        canvas_w=canvas_w,
        canvas_h=canvas_h,
        nodes=nodes,
        chrome=chrome,
        background=_COMPONENT_BACKGROUNDS.get(comp),
    )


# ── component layout functions ────────────────────────────────────────────────


def _layout_title_slide(slide: TitleSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = int(0.3 * EMU_PER_INCH)
    pad = int(0.5 * EMU_PER_INCH)

    # Operator feedback FB-018: the title reads "left-center" — left-aligned text with
    # the title(+subtitle) block vertically centred on the FULL content area, not
    # floated in the upper part of the slide.
    title_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
    sub_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT) if slide.subtitle else 0
    block_h = title_h + (gap + sub_h if slide.subtitle else 0)
    title_y = cy + max(0, (ch - block_h) // 2)
    title_rect = Rect(cx + pad, title_y, cw - 2 * pad, title_h)
    nodes.append(
        _make_text_node(_nid("title"), slide.title, font, ts.title, bold=True,
                        italic=False, rect=title_rect, color=palette.primary)
    )

    if slide.subtitle:
        sub_y = title_y + title_h + gap
        sub_rect = Rect(cx + pad, sub_y, cw - 2 * pad, sub_h)
        nodes.append(
            _make_text_node(_nid("subtitle"), slide.subtitle, font, ts.body,
                            bold=False, italic=False, rect=sub_rect)
        )

    return nodes


def _layout_icon_text_rows(slide: IconTextRowsSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    if not slide.rows:
        return nodes

    n_rows = len(slide.rows)
    available_h = cy + ch - y - gap * max(0, n_rows - 1)
    row_h = max(1, available_h // n_rows)
    # Operator feedback (issue #9): drop the filled accent "bubble" disc; the rows are
    # heading + body spanning the full width.
    text_x = cx
    text_w = cw

    line_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    # Feedback FB-010 (web #issue): the body ("subtext") was unreadable because a full
    # 0.3" gap between heading and body left the body box SHORTER than a single line, so
    # its one line was clipped. Pair the heading with its body on a tight 0.1" inner gap
    # (matching feature-list) and guarantee the body box is at least one line tall.
    inner = int(0.1 * EMU_PER_INCH)
    for i, row in enumerate(slide.rows):
        # A heading and its own body are one intentional pair (shared group_id), so the
        # tight 0.1" inner gap is exempt from E_GAP — matching feature-list.
        gid = f"itr_{i}"
        heading_h = line_h
        body_h = max(line_h, row_h - heading_h - inner)
        nodes.append(_make_text_node(_nid("heading"), row.heading, font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(text_x, y, text_w, heading_h), group_id=gid))
        nodes.append(_make_text_node(_nid("body"), row.body, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y + heading_h + inner, text_w, body_h),
                                     group_id=gid))
        y += row_h + gap

    return nodes


def _layout_stat_callout(slide: StatCalloutSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    n_stats = len(slide.stats)
    stat_w = (cw - gap * (n_stats - 1)) // n_stats if n_stats else cw
    stat_h = cy + ch - y

    # Operator feedback (issue #10): a uniform block height + shared top y so every
    # column's value (and label) align across columns, regardless of which stats carry a
    # subtext. (Previously each column self-centred its own block, so a column without a
    # subtext sat lower than its neighbours.)
    value_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
    label_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    has_sub = any(stat.subtext for stat in slide.stats)
    sub_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT) if has_sub else 0
    block_h = value_h + gap + label_h + (gap + sub_h if has_sub else 0)
    inner_y = y + max(0, (stat_h - block_h) // 2)

    for i, stat in enumerate(slide.stats):
        sx = cx + i * (stat_w + gap)
        nodes.append(_make_text_node(_nid("stat_value"), stat.value, font, ts.title,
                                     bold=True, italic=False,
                                     rect=Rect(sx, inner_y, stat_w, value_h),
                                     color=palette.accent))
        nodes.append(_make_text_node(_nid("stat_label"), stat.label, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(sx, inner_y + value_h + gap, stat_w, label_h)))
        if stat.subtext:
            nodes.append(_make_text_node(_nid("stat_sub"), stat.subtext, font, ts.caption,
                                         bold=False, italic=False,
                                         rect=Rect(sx, inner_y + value_h + gap + label_h + gap, stat_w, sub_h),
                                         is_caption=True))

    return nodes


def _layout_comparison_columns(slide: ComparisonColumnsSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    col_w = (cw - gap) // 2
    right_x = cx + col_w + gap
    col_h = cy + ch - y

    # Column headings.
    head_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    nodes.append(_make_text_node(_nid("left_head"), slide.left_title, font, ts.body,
                                 bold=True, italic=False, rect=Rect(cx, y, col_w, head_h),
                                 color=palette.primary))
    nodes.append(_make_text_node(_nid("right_head"), slide.right_title, font, ts.body,
                                 bold=True, italic=False, rect=Rect(right_x, y, col_w, head_h),
                                 color=palette.primary))
    y += head_h + gap

    # Items — use available space divided by item count to stay within canvas.
    n_items = max(len(slide.left_items), len(slide.right_items))
    available_item_h = cy + ch - y - gap * max(0, n_items)
    item_h = max(1, available_item_h // n_items) if n_items else 1
    all_items = list(zip(
        slide.left_items + [None] * max(0, len(slide.right_items) - len(slide.left_items)),
        slide.right_items + [None] * max(0, len(slide.left_items) - len(slide.right_items)),
    ))
    for left_item, right_item in all_items:
        if left_item:
            nodes.append(_make_text_node(_nid("left_item"), left_item.text, font, ts.body,
                                         bold=False, italic=False,
                                         rect=Rect(cx, y, col_w, item_h)))
        if right_item:
            nodes.append(_make_text_node(_nid("right_item"), right_item.text, font, ts.body,
                                         bold=False, italic=False,
                                         rect=Rect(right_x, y, col_w, item_h)))
        y += item_h + gap

    return nodes


def _layout_timeline(slide: TimelineSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    if not slide.events:
        return nodes

    n_events = len(slide.events)
    event_w = max(1, (cw - gap * max(0, n_events - 1)) // n_events)
    available_h = cy + ch - y
    date_h = max(1, int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT))
    title_h = max(1, int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT))
    desc_h = max(1, available_h - date_h - title_h - gap * 2)
    event_h = available_h

    for i, event in enumerate(slide.events):
        ex = cx + i * (event_w + gap)
        ey = y

        nodes.append(_make_text_node(_nid("ev_date"), event.date, font, ts.caption,
                                     bold=True, italic=False,
                                     rect=Rect(ex, ey, event_w, date_h),
                                     is_caption=True, color=palette.accent))
        ey += date_h + gap
        nodes.append(_make_text_node(_nid("ev_title"), event.title, font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(ex, ey, event_w, title_h)))
        ey += title_h + gap
        if event.description:
            nodes.append(_make_text_node(_nid("ev_desc"), event.description, font, ts.body,
                                         bold=False, italic=False,
                                         rect=Rect(ex, ey, event_w, desc_h)))

    return nodes


def _layout_image_half_bleed(slide: ImageHalfBleedSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    col_h = cy + ch - y
    img_w = cw // 2 - gap // 2
    text_w = cw - img_w - gap

    if slide.image_side == "left":
        img_x, text_x = cx, cx + img_w + gap
    else:
        text_x, img_x = cx, cx + text_w + gap

    img_rect = Rect(img_x, y, img_w, col_h)
    nodes.append(ResolvedNode(_nid("image"), "image", img_rect,
                              slot_type="image",
                              text_content=slide.image.path))

    text_nodes = _layout_content_list(slide.content, "content", text_x, y, text_w, col_h, font, ts, palette)
    nodes.extend(text_nodes)
    return nodes


def _layout_card_grid(slide: CardGridSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    n_cards = len(slide.cards)
    cols = min(4, n_cards) if n_cards > 0 else 1
    rows = (n_cards + cols - 1) // cols
    card_w = (cw - gap * (cols - 1)) // cols
    available_h = cy + ch - y
    card_h = (available_h - gap * (rows - 1)) // rows

    inner_gap = int(0.15 * EMU_PER_INCH)

    for i, card in enumerate(slide.cards):
        row_i = i // cols
        col_i = i % cols
        card_x = cx + col_i * (card_w + gap)
        card_y = y + row_i * (card_h + gap)
        gid = f"card_{i}"

        # Operator feedback (issue #12): drop the filled accent "bubble" disc; cards are
        # title + body starting at the top of the cell.
        inner_y = card_y

        title_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
        body_h = card_h - (inner_y - card_y) - title_h - inner_gap
        nodes.append(_make_text_node(_nid("card_title"), card.title, font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(card_x, inner_y, card_w, title_h),
                                     group_id=gid))
        nodes.append(_make_text_node(_nid("card_body"), card.body, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(card_x, inner_y + title_h + inner_gap,
                                               card_w, max(body_h, title_h)),
                                     group_id=gid))

    return nodes


# ── Phase 9: openers & emphasis (catalog #2–9) ────────────────────────────────
#
# These designs share a "left accent bar + vertically-centred text stack" motif.
# The accent bar is a deterministic ``box`` node (measurable, so the linter still
# proves fit) and doubles as the non-text media that keeps the slide off the
# W_TEXT_ONLY warning. The bar sits to the left of the text column with no
# horizontal overlap, so it never trips E_OVERLAP or E_GAP.

_BAR_W_EMU = int(0.14 * EMU_PER_INCH)
_BAR_INDENT_EMU = int(0.45 * EMU_PER_INCH)  # gap between bar and text column


def _emphasis_stack(items, cx, cy, cw, ch, font, palette, *, bar=True, center_on=None):
    """Lay out a vertically-centred stack of text rows with an optional left
    accent bar. ``items`` is a list of dicts: prefix/text/size, optional
    bold/italic/is_caption/color. Returns a list of ResolvedNodes.

    ``center_on`` (an item index) anchors that ROW's vertical centre on the
    field centre instead of centring the whole block — e.g. a section divider
    centres its title, letting the small number ride above it (feedback FB-014).
    """
    gap = GAP_MIN_EMU
    text_x = cx + (_BAR_W_EMU + _BAR_INDENT_EMU if bar else 0)
    text_w = cw - (_BAR_W_EMU + _BAR_INDENT_EMU if bar else 0)

    measured = []
    for it in items:
        lines = wrap(it["text"], font, it["size"], text_w,
                     bold=it.get("bold", False), italic=it.get("italic", False))
        h = max(1, total_text_height_emu(lines))
        measured.append((it, lines, h))

    total_h = sum(h for _, _, h in measured) + gap * max(0, len(measured) - 1)
    if center_on is not None and 0 <= center_on < len(measured):
        # Offset of the anchored row's top within the block, then place the block
        # so that row's centre lands on the field centre.
        before = sum(h for _, _, h in measured[:center_on]) + gap * center_on
        anchor_h = measured[center_on][2]
        y = cy + (ch // 2) - before - anchor_h // 2
        y = max(cy, y)
    else:
        y = cy + max(0, (ch - total_h) // 2)
    block_top = y

    nodes: list[ResolvedNode] = []
    for it, lines, h in measured:
        node = _make_text_node(_nid(it["prefix"]), it["text"], font, it["size"],
                               bold=it.get("bold", False), italic=it.get("italic", False),
                               rect=Rect(text_x, y, text_w, h), lines=lines,
                               is_caption=it.get("is_caption", False))
        if it.get("color"):
            node.text_color = it["color"]
        nodes.append(node)
        y += h + gap
    block_bottom = y - gap

    if bar:
        bar_node = ResolvedNode(
            _nid("accent_bar"), "box",
            Rect(cx, block_top, _BAR_W_EMU, max(1, block_bottom - block_top)),
            fill_color=palette.accent,
        )
        nodes.insert(0, bar_node)
    return nodes


def _layout_section_divider(slide: SectionDividerSlide, cx, cy, cw, ch, font, ts, palette):
    # Feedback FB-014: centre the TITLE (index 1) on the field, so the small
    # section number rides above it rather than the block centring on the number.
    return _emphasis_stack([
        {"prefix": "sec_num", "text": slide.number, "size": ts.title, "bold": True,
         "color": palette.accent},
        {"prefix": "sec_title", "text": slide.title, "size": ts.header, "bold": True},
    ], cx, cy, cw, ch, font, palette, center_on=1)


def _layout_quote_opener(slide: QuoteOpenerSlide, cx, cy, cw, ch, font, ts, palette):
    return _emphasis_stack([
        {"prefix": "quote", "text": f'"{slide.quote}"', "size": ts.header,
         "bold": False, "italic": True},
        {"prefix": "attrib", "text": f"- {slide.attribution}", "size": ts.body,
         "bold": False, "color": palette.muted},
    ], cx, cy, cw, ch, font, palette)


# Operator feedback FB-019: the hero value should DOMINATE — 1.75× the title tier
# (105pt at the default scale) — and the whole slide is centred, not bar-left.
_BIG_NUMBER_VALUE_SCALE = 1.75
_BIG_NUMBER_RULE_W_EMU = int(1.2 * EMU_PER_INCH)
_BIG_NUMBER_RULE_H_EMU = int(0.06 * EMU_PER_INCH)


def _layout_big_number(slide: BigNumberSlide, cx, cy, cw, ch, font, ts, palette):
    """One oversized centred metric: value, short accent rule, label (+ context).
    The rule is the deterministic non-text mark (replaces the left accent bar,
    which fought the centred composition — FB-019)."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    value_pt = ts.title * _BIG_NUMBER_VALUE_SCALE

    rows = [("value", slide.value, value_pt, True, palette.accent),
            ("label", slide.label, ts.header, False, None)]
    if slide.context:
        rows.append(("context", slide.context, ts.body, False, palette.muted))

    measured = []
    for prefix, text, size, bold, color in rows:
        lines = wrap(text, font, size, cw, bold=bold)
        h = max(1, total_text_height_emu(lines))
        measured.append((prefix, text, size, bold, color, lines, h))

    rule_slot = _BIG_NUMBER_RULE_H_EMU + 2 * gap  # rule sits between value and label
    total_h = sum(h for *_, h in measured) + rule_slot + gap * max(0, len(measured) - 2)
    y = cy + max(0, (ch - total_h) // 2)

    for i, (prefix, text, size, bold, color, lines, h) in enumerate(measured):
        nodes.append(_make_text_node(_nid(prefix), text, font, size, bold=bold,
                                     italic=False, rect=Rect(cx, y, cw, h), lines=lines,
                                     color=color, align="center"))
        y += h
        if i == 0:  # centred accent rule right under the value
            nodes.append(ResolvedNode(
                _nid("rule"), "box",
                Rect(cx + (cw - _BIG_NUMBER_RULE_W_EMU) // 2, y + gap,
                     _BIG_NUMBER_RULE_W_EMU, _BIG_NUMBER_RULE_H_EMU),
                fill_color=palette.accent,
            ))
            y += rule_slot
        else:
            y += gap
    return nodes


def _layout_pull_quote(slide: PullQuoteSlide, cx, cy, cw, ch, font, ts, palette):
    return _emphasis_stack([
        {"prefix": "quote", "text": f'"{slide.quote}"', "size": ts.header, "bold": True},
        {"prefix": "attrib", "text": f"- {slide.attribution}", "size": ts.body,
         "bold": False, "color": palette.muted},
    ], cx, cy, cw, ch, font, palette)


def _layout_statement(slide: StatementSlide, cx, cy, cw, ch, font, ts, palette):
    return _emphasis_stack([
        {"prefix": "statement", "text": slide.text, "size": ts.title, "bold": True},
    ], cx, cy, cw, ch, font, palette)


def _layout_definition(slide: DefinitionSlide, cx, cy, cw, ch, font, ts, palette):
    return _emphasis_stack([
        {"prefix": "term", "text": slide.term, "size": ts.title, "bold": True,
         "color": palette.accent},
        {"prefix": "def", "text": slide.definition, "size": ts.body, "bold": False},
    ], cx, cy, cw, ch, font, palette)


def _layout_question(slide: QuestionSlide, cx, cy, cw, ch, font, ts, palette):
    return _emphasis_stack([
        {"prefix": "question", "text": slide.question, "size": ts.title, "bold": True},
    ], cx, cy, cw, ch, font, palette)


def _layout_agenda(slide: AgendaSlide, cx, cy, cw, ch, font, ts, palette):
    """Title + a thin accent rule + a numbered list of items (top-aligned)."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                 bold=True, italic=False, rect=Rect(cx, y, cw, title_h)))
    y += title_h + gap

    # Thin accent rule under the title (the non-text media for this slide).
    rule_h = int(0.07 * EMU_PER_INCH)
    nodes.append(ResolvedNode(_nid("agenda_rule"), "box",
                              Rect(cx, y, cw, rule_h), fill_color=palette.accent))
    y += rule_h + gap

    n = len(slide.items)
    list_h = cy + ch - y
    # Equal vertical slots per item; text sits at the top of each slot.
    slot_h = max(1, (list_h - gap * max(0, n - 1)) // n) if n else list_h
    item_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    num_w = int(1.0 * EMU_PER_INCH)
    text_x = cx + num_w
    text_w = cw - num_w
    for i, item in enumerate(slide.items):
        gid = f"agenda_{i}"
        nodes.append(_make_text_node(_nid("ag_num"), f"{i + 1:02d}", font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(cx, y, num_w, item_h),
                                     group_id=gid, color=palette.accent))
        nodes.append(_make_text_node(_nid("ag_item"), item, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y, text_w, item_h),
                                     group_id=gid))
        y += slot_h + gap

    return nodes


# ── Phase 9: lists & text (catalog #11, #13–15) ───────────────────────────────


def _list_title(slide_title, cx, y, cw, font, ts):
    """Emit a header-tier title node; return (node, new_y)."""
    title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    node = _make_text_node(_nid("title"), slide_title, font, ts.header,
                           bold=True, italic=False, rect=Rect(cx, y, cw, title_h))
    return node, y + title_h + GAP_MIN_EMU


# Operator style rule (FB-026): "never use bullets" — list layouts carry NO bullet
# glyphs/markers; items are clean flush-left lines. A short accent rule under the
# title is the slide's deterministic non-text mark (same motif as big-number/kpi-grid).
_LIST_RULE_W_EMU = int(1.2 * EMU_PER_INCH)
_LIST_RULE_H_EMU = int(0.06 * EMU_PER_INCH)


def _layout_bullet_list(slide: BulletListSlide, cx, cy, cw, ch, font, ts, palette):
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    title_node, y = _list_title(slide.title, cx, cy, cw, font, ts)
    nodes.append(title_node)
    nodes.append(ResolvedNode(_nid("bl_rule"), "box",
                              Rect(cx, y, _LIST_RULE_W_EMU, _LIST_RULE_H_EMU),
                              fill_color=palette.accent))
    y += _LIST_RULE_H_EMU + gap

    n = len(slide.items)
    avail = cy + ch - y
    slot_h = max(1, (avail - gap * max(0, n - 1)) // n)
    item_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    for item in slide.items:
        nodes.append(_make_text_node(_nid("bl_item"), item, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(cx, y, cw, item_h)))
        y += slot_h + gap
    return nodes


# ── code / terminal block (dark, full-bleed, monospace) ───────────────────────
# A distinct skeleton: the whole slide is a near-black IDE/terminal panel that bleeds
# edge-to-edge, optional macOS-style window dots, and the source rendered verbatim in a
# metric-safe monospace font (Courier New) — each newline is a hard line break (no
# wrapping), indentation preserved. Comment lines (`#…`) are dimmed; everything else is
# the light foreground. Deterministic and measurable: the linter still proves every line
# fits. (Repurposed from the former `checklist` layout — operator issue #14.)
# Token colours follow the VS Code Dark+ Python theme (operator feedback FB-027:
# "text color needs to match modern IDE color usage"). Highlighting is a small
# DETERMINISTIC per-line tokenizer (regex, no external highlighter): same source in,
# same coloured runs out — each run is its own measured text node, so the linter
# still proves every line fits.
_CODE_BG = "#1E1E1E"       # VS Code Dark+ editor background
_CODE_FG = "#D4D4D4"       # default foreground / punctuation
_CODE_COMMENT = "#6A9955"  # comments
_CODE_KEYWORD = "#C586C0"  # control-flow keywords (if/for/return/...)
_CODE_DECL = "#569CD6"     # declaration keywords + constants (def/class/import/None/...)
_CODE_STRING = "#CE9178"   # string literals
_CODE_NUMBER = "#B5CEA8"   # numeric literals
_CODE_FUNC = "#DCDCAA"     # function names at def sites and call sites
_CODE_PROMPT = "#4EC9B0"   # the "$" sigil on terminal lines
_CODE_TITLE = "#858585"    # filename tab (Dark+ line-number gray)
_CODE_DOTS = ("#FF5F56", "#FFBD2E", "#27C93F")  # macOS window traffic lights
_CODE_FONT = "courier new"

_PY_CONTROL = frozenset("if elif else for while try except finally with return yield "
                        "break continue pass raise assert del match case".split())
_PY_DECL = frozenset("def class import from as lambda global nonlocal async await "
                     "True False None self in not and or is".split())

_CODE_TOKEN_RE = re.compile(
    r"""(?P<comment>\#.*$)
      | (?P<string>[rbfuRBFU]{0,2}(?:'[^']*'|"[^"]*"))
      | (?P<number>\b\d+(?:\.\d+)?\b)
      | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
      | (?P<other>.)""",
    re.VERBOSE,
)


def _code_line_runs(raw: str) -> list[tuple[str, str]]:
    """Tokenize one source line into (text, colour) runs, VS Code Dark+ style.
    Deterministic and total: every character lands in exactly one run; adjacent
    runs with the same colour are merged."""
    stripped = raw.lstrip()
    if stripped.startswith("#"):
        return [(raw, _CODE_COMMENT)]
    if stripped.startswith("$"):
        sigil_end = raw.index("$") + 1
        return [(raw[:sigil_end], _CODE_PROMPT), (raw[sigil_end:], _CODE_FG)] \
            if raw[sigil_end:] else [(raw, _CODE_PROMPT)]

    runs: list[tuple[str, str]] = []
    prev_was_def = False
    for m in _CODE_TOKEN_RE.finditer(raw):
        text = m.group(0)
        if m.lastgroup == "comment":
            color = _CODE_COMMENT
        elif m.lastgroup == "string":
            color = _CODE_STRING
        elif m.lastgroup == "number":
            color = _CODE_NUMBER
        elif m.lastgroup == "name":
            if text in _PY_CONTROL:
                color = _CODE_KEYWORD
            elif text in _PY_DECL:
                color = _CODE_DECL
            elif prev_was_def or raw[m.end():m.end() + 1] == "(":
                color = _CODE_FUNC  # def-site or call-site function name
            else:
                color = _CODE_FG
            prev_was_def = text in ("def", "class")
        else:
            color = _CODE_FG
        if runs and runs[-1][1] == color:
            runs[-1] = (runs[-1][0] + text, color)
        else:
            runs.append((text, color))
    return runs or [(raw, _CODE_FG)]

# Components whose slide carries an intrinsic full-canvas background (painted by the
# emitter as a first-class backdrop, not a content node). Keyed by component.
_COMPONENT_BACKGROUNDS = {"code": _CODE_BG}


def _layout_code(slide: CodeSlide, cx, cy, cw, ch, font, ts, palette):
    nodes: list[ResolvedNode] = []
    gid = "code"
    y = cy

    # The dark panel is the slide's first-class background (see _COMPONENT_BACKGROUNDS),
    # painted edge-to-edge by the emitter — not a node here, so no margin/overlap hacks.

    # macOS-style window dots.
    if slide.chrome:
        dot = int(0.16 * EMU_PER_INCH)
        dgap = int(0.12 * EMU_PER_INCH)
        for i, color in enumerate(_CODE_DOTS):
            dx = cx + i * (dot + dgap)
            nodes.append(ResolvedNode(_nid("code_dot"), "box", Rect(dx, y, dot, dot),
                                      fill_color=color, group_id=gid))
        y += dot + int(0.35 * EMU_PER_INCH)

    # Optional filename / caption.
    if slide.title:
        cap_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
        nodes.append(_make_text_node(_nid("code_title"), slide.title, _CODE_FONT, ts.caption,
                                     bold=True, italic=False, rect=Rect(cx, y, cw, cap_h),
                                     is_caption=True, color=_CODE_TITLE, group_id=gid))
        y += cap_h + GAP_MIN_EMU

    # Code lines: verbatim, monospace, no wrapping; syntax-coloured per token (FB-027).
    # Each coloured run is its own measured node placed at the run's exact x offset.
    # Emitters draw glyphs at rect.x + INSET_LEFT, so a run's rect.x is its glyph
    # offset MINUS nothing for the first run (rect.x = cx + prefix width keeps every
    # glyph exactly where the old single-node line put it) and the rect is widened by
    # the insets so no emitter re-wraps. Runs of a line overlap by the insets — they
    # share the "code" group_id, so E_OVERLAP/E_GAP treat the line as one intentional
    # unit (exactly as the whole block already did). Blank lines advance the cursor.
    size = ts.body
    line_h = int(size * LINE_SPACING_SINGLE * EMU_PER_PT)
    for raw in slide.code.split("\n"):
        if raw.strip():
            line_w = measure_text(raw, _CODE_FONT, size)
            prefix = ""
            for text, color in _code_line_runs(raw):
                run_w = measure_text(text, _CODE_FONT, size)
                line = Line(text=text, width_emu=run_w, height_emu=line_h,
                            overflows=line_w > cw)
                # x from measuring the ACTUAL prefix substring (not accumulated run
                # widths) so per-call rounding can never drift across a line.
                nodes.append(_make_text_node(
                    _nid("code_run"), text, _CODE_FONT, size, bold=False, italic=False,
                    rect=Rect(cx + measure_text(prefix, _CODE_FONT, size), y,
                              run_w + INSET_LEFT_EMU + INSET_RIGHT_EMU, line_h),
                    lines=[line], color=color, group_id=gid))
                prefix += text
        y += line_h
    return nodes


def _layout_feature_list(slide: FeatureListSlide, cx, cy, cw, ch, font, ts, palette):
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy
    if slide.title:
        title_node, y = _list_title(slide.title, cx, cy, cw, font, ts)
        nodes.append(title_node)

    n = len(slide.features)
    avail = cy + ch - y
    slot_h = max(1, (avail - gap * max(0, n - 1)) // n)
    # Operator feedback (issue #13): drop the filled accent "bubble" disc; each feature is
    # heading + body spanning the full width.
    text_x = cx
    text_w = cw
    heading_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    inner = int(0.1 * EMU_PER_INCH)
    for i, feat in enumerate(slide.features):
        gid = f"feat_{i}"
        nodes.append(_make_text_node(_nid("feat_head"), feat.heading, font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(text_x, y, text_w, heading_h), group_id=gid))
        body_h = max(1, slot_h - heading_h - inner)
        nodes.append(_make_text_node(_nid("feat_body"), feat.body, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y + heading_h + inner, text_w, body_h),
                                     group_id=gid))
        y += slot_h + gap
    return nodes


def _layout_numbered_steps(slide: NumberedStepsSlide, cx, cy, cw, ch, font, ts, palette):
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy
    if slide.title:
        title_node, y = _list_title(slide.title, cx, cy, cw, font, ts)
        nodes.append(title_node)

    n = len(slide.steps)
    avail = cy + ch - y
    slot_h = max(1, (avail - gap * max(0, n - 1)) // n)
    chip = int(0.6 * EMU_PER_INCH)
    text_x = cx + chip + int(0.25 * EMU_PER_INCH)
    text_w = cw - chip - int(0.25 * EMU_PER_INCH)
    heading_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    inner = int(0.1 * EMU_PER_INCH)
    for i, step in enumerate(slide.steps):
        gid = f"step_{i}"
        # Numbered chip: accent box with the step number on top (same group, so the
        # intentional text-on-box stack is exempt from E_OVERLAP).
        nodes.append(ResolvedNode(_nid("step_chip"), "box", Rect(cx, y, chip, chip),
                                  fill_color=palette.accent, group_id=gid))
        nodes.append(_make_text_node(_nid("step_num"), str(i + 1), font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(cx, y, chip, chip), group_id=gid,
                                     color=palette.surface))
        nodes.append(_make_text_node(_nid("step_head"), step.title, font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(text_x, y, text_w, heading_h), group_id=gid))
        body_h = max(1, slot_h - heading_h - inner)
        nodes.append(_make_text_node(_nid("step_body"), step.body, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y + heading_h + inner, text_w, body_h),
                                     group_id=gid))
        y += slot_h + gap
    return nodes


# ── Phase 9: comparison (catalog #17–19) ──────────────────────────────────────


def _panel_items(nodes, items, x, y, w, h, font, ts, marker_color, prefix,
                 item_pt=None, is_caption=False, group_id=None):
    """Render a column of items as clean flush-left lines — NO bullet markers
    (operator style rule FB-026: "never use bullets"). ``marker_color`` is kept in
    the signature for callers that colour their panel headings/rules with it.

    ``item_pt`` overrides the item type-tier (default: body). Dense grid callers
    (swot) pass the caption tier + ``is_caption`` so each item box can honestly hold
    a full leaded line inside a short cell — without this the ``min(slot_h, …)`` cap
    below would clamp the box under one line (board T-064)."""
    gap = GAP_MIN_EMU
    n = len(items)
    slot_h = max(1, (h - gap * max(0, n - 1)) // n)
    item_pt = ts.body if item_pt is None else item_pt
    line_h = int(item_pt * LINE_SPACING_SINGLE * EMU_PER_PT)
    cur = y
    for item in items:
        # Size each item box to its wrapped height (column is narrow → items may
        # wrap), floored at one leaded line and capped at the slot so consecutive
        # rows never collide.
        lines = wrap(item, font, item_pt, w)
        item_h = min(slot_h, max(line_h, total_text_height_emu(lines)))
        nodes.append(_make_text_node(_nid(f"{prefix}_item"), item, font, item_pt,
                                     bold=False, italic=False,
                                     rect=Rect(x, cur, w, item_h), lines=lines,
                                     is_caption=is_caption, group_id=group_id))
        cur += slot_h + gap


def _two_panel_list(title, left_head, left_items, left_color,
                    right_head, right_items, right_color,
                    cx, cy, cw, ch, font, ts, palette):
    """Two side-by-side titled bullet columns. Headings carry the panel's accent/muted
    colour to signal the contrast (e.g. before↔after, pros↔cons); item text stays in
    the default colour for readability. The markers are the non-text media."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy
    if title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), title, font, ts.header, bold=True,
                                     italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    col_w = (cw - gap) // 2
    right_x = cx + col_w + gap
    head_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    rule_h = int(0.06 * EMU_PER_INCH)
    inner = int(0.12 * EMU_PER_INCH)
    for px, head, color, prefix in ((cx, left_head, left_color, "lp"),
                                    (right_x, right_head, right_color, "rp")):
        gid = f"{prefix}_head"
        nodes.append(_make_text_node(_nid(f"{prefix}_head"), head, font, ts.body, bold=True,
                                     italic=False, rect=Rect(px, y, col_w, head_h),
                                     color=color, group_id=gid))
        # Panel-coloured rule under the heading: carries the muted-vs-accent contrast
        # without bullet markers (FB-026) and is the panel's non-text mark. It rides
        # INSIDE the existing heading->items gap (panel-wide group_id makes the tight
        # spacing intentional), so the items keep every EMU of space they had.
        nodes.append(ResolvedNode(_nid(f"{prefix}_rule"), "box",
                                  Rect(px, y + head_h + inner,
                                       max(1, int(col_w * 0.3)), rule_h),
                                  fill_color=color, group_id=gid))
    items_y = y + head_h + gap
    items_h = cy + ch - items_y
    _panel_items(nodes, left_items, cx, items_y, col_w, items_h, font, ts, left_color, "lp",
                 group_id="lp_head")
    _panel_items(nodes, right_items, right_x, items_y, col_w, items_h, font, ts, right_color, "rp",
                 group_id="rp_head")
    return nodes


def _layout_two_panel_list(slide: TwoPanelListSlide, cx, cy, cw, ch, font, ts, palette):
    """Two contrasting states head-to-head (before/after, pros/cons, old/new):
    left panel muted, right panel accent — a deterministic left→right contrast read."""
    return _two_panel_list(
        slide.title,
        slide.left.title, slide.left.items, palette.muted,
        slide.right.title, slide.right.items, palette.accent,
        cx, cy, cw, ch, font, ts, palette,
    )


def _layout_this_vs_that(slide: ThisVsThatSlide, cx, cy, cw, ch, font, ts, palette):
    """Two headline numbers head-to-head with a central VS badge (a measurable box
    with the text 'VS' on top — also the slide's non-text media)."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy
    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header, bold=True,
                                     italic=False, rect=Rect(cx, y, cw, title_h),
                                     color=palette.primary))
        y += title_h + gap

    # Operator feedback FB-028 (supersedes the FB-023 badge rework): the accent/primary
    # value colours read as jarring and the boxed VS was unwanted. Now: ALL text in the
    # default text colour, and "VS" is a bare muted caption centred between the columns
    # on the value+label block midline — no box, no fills. The slide is deliberately
    # text-only (exempted from W_TEXT_ONLY in the linter).
    mid_w = int(0.75 * EMU_PER_INCH)  # breathing room between the columns
    col_w = (cw - mid_w - 2 * gap) // 2
    left_x = cx
    right_x = cx + col_w + gap + mid_w + gap
    content_h = cy + ch - y

    value_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
    label_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    block_h = value_h + gap + label_h
    inner_y = y + max(0, (content_h - block_h) // 2)

    for px, side in ((left_x, slide.left), (right_x, slide.right)):
        nodes.append(_make_text_node(_nid("vs_value"), side.value, font, ts.title, bold=True,
                                     italic=False, rect=Rect(px, inner_y, col_w, value_h),
                                     align="center"))
        nodes.append(_make_text_node(_nid("vs_label"), side.label, font, ts.body, bold=False,
                                     italic=False,
                                     rect=Rect(px, inner_y + value_h + gap, col_w, label_h),
                                     align="center"))

    # Bare "VS", centred between the columns on the block midline.
    vs_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
    vs_x = cx + (cw - mid_w) // 2
    vs_y = inner_y + max(0, (block_h - vs_h) // 2)
    nodes.append(_make_text_node(_nid("vs_text"), "VS", font, ts.caption, bold=True,
                                 italic=False, rect=Rect(vs_x, vs_y, mid_w, vs_h),
                                 is_caption=True, align="center"))
    return nodes


# ── Phase 9: data & stats (catalog #21–25) ────────────────────────────────────
#
# These designs render quantitative content with measurable rects only: KPI cells
# with an accent underline, charts as colored bar rectangles + labels (never
# freehand strokes), tables as a cell grid with an accent header rule, and metric
# deltas as small accent chips. Every mark is a node the linter can prove fits.


def _slide_title(nodes, title, cx, y, cw, font, ts, palette):
    """Emit a header-tier slide title (brand primary) if present; return new y."""
    if not title:
        return y
    title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    nodes.append(_make_text_node(_nid("title"), title, font, ts.header, bold=True,
                                 italic=False, rect=Rect(cx, y, cw, title_h),
                                 color=palette.primary))
    return y + title_h + GAP_MIN_EMU


def _fmt_num(v: float) -> str:
    """Format a chart value: drop a trailing .0 on integers, else keep as-is."""
    return str(int(v)) if float(v).is_integer() else str(v)


def _chart_nodes(chart, x, y, w, h, font, ts, palette, prefix) -> list[ResolvedNode]:
    """Render a chart slot deterministically. Bar charts become measured accent
    rectangles with a value label above and a category label below each bar; other
    chart types render as a single labelled placeholder region. No freehand marks —
    every element is a rect the linter can verify, per the Phase 9 shape rule."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    if chart.chart_type == "bar" and chart.series and chart.series[0].values:
        values = chart.series[0].values
        labels = chart.labels or [str(i + 1) for i in range(len(values))]
        n = len(values)
        val_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
        cat_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
        bars_area_h = max(1, h - val_h - cat_h - 2 * gap)
        slot_w = max(1, (w - gap * max(0, n - 1)) // n)
        bar_w = max(1, int(slot_w * 0.7))
        bar_pad = (slot_w - bar_w) // 2
        maxv = max(values)
        maxv = maxv if maxv > 0 else 1
        baseline_y = y + val_h + gap + bars_area_h
        for i, v in enumerate(values):
            gid = f"{prefix}_bar_{i}"
            slot_x = x + i * (slot_w + gap)
            bh = max(1, int(bars_area_h * (v / maxv)))
            by = baseline_y - bh
            nodes.append(_make_text_node(_nid(f"{prefix}_val"), _fmt_num(v), font,
                                         ts.caption, bold=True, italic=False,
                                         rect=Rect(slot_x, by - val_h - gap, slot_w, val_h),
                                         is_caption=True, color=palette.accent, group_id=gid))
            nodes.append(ResolvedNode(_nid(f"{prefix}_barbox"), "box",
                                      Rect(slot_x + bar_pad, by, bar_w, bh),
                                      fill_color=palette.accent, group_id=gid))
            cat = labels[i] if i < len(labels) else str(i + 1)
            nodes.append(_make_text_node(_nid(f"{prefix}_cat"), cat, font, ts.caption,
                                         bold=False, italic=False,
                                         rect=Rect(slot_x, baseline_y + gap, slot_w, cat_h),
                                         is_caption=True, color=palette.muted, group_id=gid))
        return nodes

    # Non-bar fallback: a single labelled region (muted fill, label on top).
    gid = f"{prefix}_region"
    nodes.append(ResolvedNode(_nid(f"{prefix}_box"), "box", Rect(x, y, w, h),
                              fill_color=palette.muted, group_id=gid))
    label = chart.title or f"{chart.chart_type} chart"
    lbl_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    nodes.append(_make_text_node(_nid(f"{prefix}_label"), label, font, ts.body, bold=True,
                                 italic=False,
                                 rect=Rect(x, y + max(0, (h - lbl_h) // 2), w, lbl_h),
                                 color=palette.surface, group_id=gid))
    return nodes


def _layout_kpi_grid(slide: KpiGridSlide, cx, cy, cw, ch, font, ts, palette):
    """Dashboard of small metrics: a grid of cells, each a header-tier value (accent)
    over a short accent underline over a body-tier label. The underline is the
    deterministic non-text accent that signals a dashboard tile."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.kpis)
    cols = min(3, n)
    rows = (n + cols - 1) // cols
    cell_w = (cw - gap * (cols - 1)) // cols
    avail = cy + ch - y
    cell_h = (avail - gap * (rows - 1)) // rows if rows else avail

    # Operator feedback FB-024: full 0.3" sibling gaps INSIDE a tile pulled the
    # value / rule / label apart until the grid read as loose scatter. A tile is one
    # intentional group (shared group_id, so tight gaps are lint-exempt): use a 0.12"
    # inner gap, centre the rule under the value, and centre the tile's text so each
    # cell reads as a compact dashboard tile.
    inner = int(0.12 * EMU_PER_INCH)
    value_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT)
    rule_h = int(0.06 * EMU_PER_INCH)
    rule_w = max(1, int(cell_w * 0.3))
    for i, kpi in enumerate(slide.kpis):
        gid = f"kpi_{i}"
        r, c = divmod(i, cols)
        kx = cx + c * (cell_w + gap)
        ky = y + r * (cell_h + gap)
        # Size the label box to its measured wrapped height so it never overflows;
        # centre the value/rule/label block within the cell.
        label_lines = wrap(kpi.label, font, ts.body, cell_w)
        label_h = max(1, total_text_height_emu(label_lines))
        block_h = value_h + inner + rule_h + inner + label_h
        inner_y = ky + max(0, (cell_h - block_h) // 2)
        nodes.append(_make_text_node(_nid("kpi_val"), kpi.value, font, ts.header, bold=True,
                                     italic=False, rect=Rect(kx, inner_y, cell_w, value_h),
                                     color=palette.accent, group_id=gid, align="center"))
        ry = inner_y + value_h + inner
        nodes.append(ResolvedNode(_nid("kpi_rule"), "box",
                                  Rect(kx + (cell_w - rule_w) // 2, ry, rule_w, rule_h),
                                  fill_color=palette.accent, group_id=gid))
        ly = ry + rule_h + inner
        nodes.append(_make_text_node(_nid("kpi_label"), kpi.label, font, ts.body, bold=False,
                                     italic=False, rect=Rect(kx, ly, cell_w, label_h),
                                     lines=label_lines, group_id=gid, align="center"))
    return nodes


def _layout_chart_with_insight(slide: ChartWithInsightSlide, cx, cy, cw, ch, font, ts, palette):
    """Chart on the left, a takeaway callout (accent bar + bold text) on the right."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    content_h = cy + ch - y
    chart_w = int(cw * 0.6)
    insight_x = cx + chart_w + gap
    insight_w = cw - chart_w - gap
    nodes.extend(_chart_nodes(slide.chart, cx, y, chart_w, content_h, font, ts, palette, "chart"))
    nodes.extend(_emphasis_stack(
        [{"prefix": "insight", "text": slide.insight, "size": ts.body, "bold": True}],
        insight_x, y, insight_w, content_h, font, palette,
    ))
    return nodes


def _layout_table_slide(slide: TableSlide, cx, cy, cw, ch, font, ts, palette):
    """A small text table: a bold header row (brand primary) over an accent rule,
    then a grid of body-tier cells. The rule is the deterministic non-text mark."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    ncols = len(slide.headers)
    col_w = (cw - gap * (ncols - 1)) // ncols if ncols else cw
    head_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    rule_h = int(0.06 * EMU_PER_INCH)

    for c, htext in enumerate(slide.headers):
        hx = cx + c * (col_w + gap)
        nodes.append(_make_text_node(_nid("th"), htext, font, ts.body, bold=True,
                                     italic=False, rect=Rect(hx, y, col_w, head_h),
                                     color=palette.primary))
    ry = y + head_h + gap
    nodes.append(ResolvedNode(_nid("table_rule"), "box", Rect(cx, ry, cw, rule_h),
                              fill_color=palette.accent))
    yy = ry + rule_h + gap

    nrows = len(slide.rows)
    body_h = cy + ch - yy
    row_h = max(1, (body_h - gap * max(0, nrows - 1)) // nrows) if nrows else body_h
    for r, row in enumerate(slide.rows):
        for c in range(ncols):
            cell = row[c] if c < len(row) else ""
            cxx = cx + c * (col_w + gap)
            nodes.append(_make_text_node(_nid("td"), cell, font, ts.body, bold=False,
                                         italic=False, rect=Rect(cxx, yy, col_w, row_h)))
        yy += row_h + gap
    return nodes


def _layout_metric_comparison(slide: MetricComparisonSlide, cx, cy, cw, ch, font, ts, palette):
    """2–3 metrics side by side: a title-tier value (accent), a body label, and an
    optional change delta rendered as a small accent chip (box + label on top)."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.metrics)
    col_w = (cw - gap * (n - 1)) // n if n else cw
    col_h = cy + ch - y
    value_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
    delta_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    chip_pad = int(0.18 * EMU_PER_INCH)

    for i, m in enumerate(slide.metrics):
        gid = f"metric_{i}"
        mx = cx + i * (col_w + gap)
        has_delta = m.delta is not None
        # Size the label box to its measured wrapped height; centre the block.
        label_lines = wrap(m.label, font, ts.body, col_w)
        label_h = max(1, total_text_height_emu(label_lines))
        block_h = value_h + gap + label_h + (gap + delta_h if has_delta else 0)
        inner_y = y + max(0, (col_h - block_h) // 2)
        nodes.append(_make_text_node(_nid("metric_val"), m.value, font, ts.title, bold=True,
                                     italic=False, rect=Rect(mx, inner_y, col_w, value_h),
                                     color=palette.accent))
        ly = inner_y + value_h + gap
        nodes.append(_make_text_node(_nid("metric_label"), m.label, font, ts.body, bold=False,
                                     italic=False, rect=Rect(mx, ly, col_w, label_h),
                                     lines=label_lines))
        if has_delta:
            dy = ly + label_h + gap
            chip_w = min(col_w, measure_text(m.delta, font, ts.body, bold=True) + 2 * chip_pad)
            nodes.append(ResolvedNode(_nid("metric_chip"), "box", Rect(mx, dy, chip_w, delta_h),
                                      fill_color=palette.accent, group_id=gid))
            nodes.append(_make_text_node(_nid("metric_delta"), m.delta, font, ts.body, bold=True,
                                         italic=False, rect=Rect(mx, dy, chip_w, delta_h),
                                         color=palette.surface, group_id=gid))
    return nodes


# ── Phase 9: process & shape (catalog #26, 28–32) ─────────────────────────────
#
# Process and shape designs render structure with measured rects only — numbered
# chips, lane header bands, narrowing/widening bars, and a centered axis cross.
# Funnels, pyramids and quadrants are colored rectangles with labels (never
# freehand connectors), so the linter still proves every element fits.


def _layout_process_steps(slide: ProcessStepsSlide, cx, cy, cw, ch, font, ts, palette):
    """Horizontal numbered flow: N columns, each a numbered accent chip over a bold
    label (brand primary) and a body description. The chips carry the sequence; no
    connector lines are drawn (deterministic)."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.steps)
    col_w = (cw - gap * (n - 1)) // n if n else cw
    col_h = cy + ch - y
    chip = int(0.6 * EMU_PER_INCH)
    label_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    inner = int(0.1 * EMU_PER_INCH)
    for i, step in enumerate(slide.steps):
        gid = f"pstep_{i}"
        sx = cx + i * (col_w + gap)
        # Numbered chip: accent box with the step number on top (same group, so the
        # intentional text-on-box stack is exempt from E_OVERLAP).
        nodes.append(ResolvedNode(_nid("ps_chip"), "box", Rect(sx, y, chip, chip),
                                  fill_color=palette.accent, group_id=gid))
        nodes.append(_make_text_node(_nid("ps_num"), str(i + 1), font, ts.body, bold=True,
                                     italic=False, rect=Rect(sx, y, chip, chip),
                                     group_id=gid, color=palette.surface))
        # Label + body are one step's text block, grouped with the chip so the tight
        # internal spacing is exempt from E_GAP (the same pattern as numbered-steps).
        ly = y + chip + gap
        nodes.append(_make_text_node(_nid("ps_label"), step.label, font, ts.body, bold=True,
                                     italic=False, rect=Rect(sx, ly, col_w, label_h),
                                     color=palette.primary, group_id=gid))
        by = ly + label_h + inner
        body_h = max(1, y + col_h - by)
        nodes.append(_make_text_node(_nid("ps_body"), step.body, font, ts.body, bold=False,
                                     italic=False, rect=Rect(sx, by, col_w, body_h),
                                     group_id=gid))
    return nodes


def _layout_roadmap(slide: RoadmapSlide, cx, cy, cw, ch, font, ts, palette):
    """Phased plan across vertical lanes: each phase is a column with an accent
    header band (title on top, surface text) over a bulleted list of items."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.phases)
    col_w = (cw - gap * (n - 1)) // n if n else cw
    col_h = cy + ch - y
    head_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    for i, ph in enumerate(slide.phases):
        gid = f"phase_{i}"
        px = cx + i * (col_w + gap)
        # Header band: accent box with the phase title on top (grouped).
        nodes.append(ResolvedNode(_nid("rm_head"), "box", Rect(px, y, col_w, head_h),
                                  fill_color=palette.accent, group_id=gid))
        nodes.append(_make_text_node(_nid("rm_title"), ph.title, font, ts.body, bold=True,
                                     italic=False, rect=Rect(px, y, col_w, head_h),
                                     group_id=gid, color=palette.surface))
        items_y = y + head_h + gap
        items_h = y + col_h - items_y
        _panel_items(nodes, ph.items, px, items_y, col_w, items_h, font, ts,
                     palette.accent, f"rm{i}")
    return nodes


def _layout_funnel(slide: FunnelSlide, cx, cy, cw, ch, font, ts, palette):
    """Narrowing stages: a vertical stack of centered accent bars, each narrower
    than the one above, with the stage label (and optional value) on top. The bars
    are measured rects — the narrowing is the deterministic funnel read."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.stages)
    avail = cy + ch - y
    band_h = max(1, (avail - gap * max(0, n - 1)) // n)
    min_frac = 0.45
    for i, st in enumerate(slide.stages):
        gid = f"funnel_{i}"
        frac = 1.0 - (1.0 - min_frac) * (i / (n - 1)) if n > 1 else 1.0
        bw = max(1, int(cw * frac))
        bx = cx + (cw - bw) // 2
        by = y + i * (band_h + gap)
        nodes.append(ResolvedNode(_nid("fn_bar"), "box", Rect(bx, by, bw, band_h),
                                  fill_color=palette.accent, group_id=gid))
        text = f"{st.label} · {st.value}" if st.value else st.label
        nodes.append(_make_text_node(_nid("fn_label"), text, font, ts.body, bold=True,
                                     italic=False, rect=Rect(bx, by, bw, band_h),
                                     group_id=gid, color=palette.surface))
    return nodes


def _layout_pyramid(slide: PyramidSlide, cx, cy, cw, ch, font, ts, palette):
    """Layered hierarchy: stacked bars widening toward the base, alternating brand
    primary and accent fills, each layer's label on top. Measured rects only — the
    widening is the deterministic pyramid read."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.layers)
    avail = cy + ch - y
    band_h = max(1, (avail - gap * max(0, n - 1)) // n)
    min_frac = 0.4
    for i, layer in enumerate(slide.layers):
        gid = f"pyr_{i}"
        # Top (i=0) narrowest, base (i=n-1) widest.
        frac = min_frac + (1.0 - min_frac) * (i / (n - 1)) if n > 1 else 1.0
        bw = max(1, int(cw * frac))
        bx = cx + (cw - bw) // 2
        by = y + i * (band_h + gap)
        fill = palette.primary if i % 2 == 0 else palette.accent
        nodes.append(ResolvedNode(_nid("pyr_bar"), "box", Rect(bx, by, bw, band_h),
                                  fill_color=fill, group_id=gid))
        nodes.append(_make_text_node(_nid("pyr_label"), layer.label, font, ts.body, bold=True,
                                     italic=False, rect=Rect(bx, by, bw, band_h),
                                     group_id=gid, color=palette.surface))
    return nodes


def _layout_matrix_2x2(slide: Matrix2x2Slide, cx, cy, cw, ch, font, ts, palette):
    """Quadrant positioning: a 2×2 field split by a centered accent cross (one
    horizontal + one vertical rule, grouped so their intersection is intentional),
    each quadrant holding its label, with the axis names as captions. The cross
    rules are the measured non-text marks."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    cap_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
    field_y = y + cap_h + gap
    field_bottom = cy + ch - cap_h - gap
    field_h = max(1, field_bottom - field_y)

    # Axis captions: y-axis name across the top, x-axis name across the bottom.
    nodes.append(_make_text_node(_nid("mx_y"), slide.y_label, font, ts.caption, bold=True,
                                 italic=False, rect=Rect(cx, y, cw, cap_h),
                                 is_caption=True, color=palette.muted))
    nodes.append(_make_text_node(_nid("mx_x"), slide.x_label, font, ts.caption, bold=False,
                                 italic=False, rect=Rect(cx, field_bottom + gap, cw, cap_h),
                                 is_caption=True, color=palette.muted))

    rule = int(0.05 * EMU_PER_INCH)
    midx = cx + cw // 2
    midy = field_y + field_h // 2
    nodes.append(ResolvedNode(_nid("mx_vrule"), "box",
                              Rect(midx - rule // 2, field_y, rule, field_h),
                              fill_color=palette.accent, group_id="mx_cross"))
    nodes.append(ResolvedNode(_nid("mx_hrule"), "box",
                              Rect(cx, midy - rule // 2, cw, rule),
                              fill_color=palette.accent, group_id="mx_cross"))

    # Quadrant cells, inset from the cross by >= gap so neither E_GAP nor E_OVERLAP
    # trips against the rules.
    cell_w = cw // 2 - gap - rule
    cell_h = field_h // 2 - gap - rule
    positions = [
        (cx, field_y),                            # top-left
        (midx + rule + gap, field_y),             # top-right
        (cx, midy + rule + gap),                  # bottom-left
        (midx + rule + gap, midy + rule + gap),   # bottom-right
    ]
    for i, q in enumerate(slide.quadrants):
        qx, qy = positions[i]
        nodes.append(_make_text_node(_nid("mx_q"), q, font, ts.body, bold=False,
                                     italic=False, rect=Rect(qx, qy, cell_w, cell_h)))
    return nodes


def _layout_swot(slide: SwotSlide, cx, cy, cw, ch, font, ts, palette):
    """SWOT 2×2: four titled quadrants — Strengths/Opportunities headed in accent,
    Weaknesses/Threats in muted — each a heading over a bulleted list. Markers are
    the non-text media; no quadrant background fills (restraint over ornament)."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    col_w = (cw - gap) // 2
    field_h = cy + ch - y
    cell_h = (field_h - gap) // 2
    quads = [
        ("Strengths", slide.strengths, palette.accent, cx, y),
        ("Weaknesses", slide.weaknesses, palette.muted, cx + col_w + gap, y),
        ("Opportunities", slide.opportunities, palette.accent, cx, y + cell_h + gap),
        ("Threats", slide.threats, palette.muted, cx + col_w + gap, y + cell_h + gap),
    ]
    head_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
    rule_h = int(0.06 * EMU_PER_INCH)
    inner = int(0.12 * EMU_PER_INCH)
    for idx, (head, items, color, qx, qy) in enumerate(quads):
        gid = f"swot_head_{idx}"
        nodes.append(_make_text_node(_nid("swot_head"), head, font, ts.body, bold=True,
                                     italic=False, rect=Rect(qx, qy, col_w, head_h),
                                     color=color, group_id=gid))
        # Quadrant-coloured rule under the heading — the colour cue + non-text mark
        # now that list markers are gone (FB-026). Rides inside the existing
        # heading->items gap (shared gid) so quadrant items lose no space.
        nodes.append(ResolvedNode(_nid("swot_rule"), "box",
                                  Rect(qx, qy + head_h + inner,
                                       max(1, int(col_w * 0.3)), rule_h),
                                  fill_color=color, group_id=gid))
        items_y = qy + head_h + gap
        items_h = qy + cell_h - items_y
        # SWOT packs four bulleted lists into a 2×2 grid, so each quadrant cell is
        # short. Item text uses the caption tier (secondary, dense grid content) so
        # every item box honestly holds a full leaded line inside the cell rather
        # than being clamped under one line (board T-064). Bold body headings still
        # dominate the tier hierarchy.
        _panel_items(nodes, items, qx, items_y, col_w, items_h, font, ts, color,
                     f"swot{idx}", item_pt=ts.caption, is_caption=True, group_id=gid)
    return nodes



# ── Phase 9: structured relationships & visual (catalog #33, #35, #37–40) ────
#
# These last six designs stay within the same deterministic rules as the rest of
# Phase 9: images/logos are measured placeholder rects, grids use explicit cells,
# and overlay text shares a group_id with its background/image where overlap is the
# intended visual stack.


def _layout_comparison_matrix(slide: ComparisonMatrixSlide, cx, cy, cw, ch, font, ts, palette):
    """Features × options grid: criteria down the left, options across the top,
    and deterministic text cells with a muted fill. Header cells use brand colour."""
    nodes: list[ResolvedNode] = []
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n_options = len(slide.options)
    n_criteria = len(slide.criteria)
    label_w = int(cw * 0.28)
    cell_w = max(1, (cw - label_w) // n_options) if n_options else cw - label_w
    rows = n_criteria + 1
    row_h = max(1, (cy + ch - y) // rows) if rows else cy + ch - y

    # Top-left header block anchors the matrix and provides a non-text element.
    nodes.append(ResolvedNode(_nid("cm_corner"), "box", Rect(cx, y, label_w, row_h),
                              fill_color=palette.primary, group_id="cm_corner"))
    nodes.append(_make_text_node(_nid("cm_corner_text"), "Criteria", font, ts.body,
                                 bold=True, italic=False, rect=Rect(cx, y, label_w, row_h),
                                 color=palette.surface, group_id="cm_corner"))
    for c, opt in enumerate(slide.options):
        gid = f"cm_head_{c}"
        x = cx + label_w + c * cell_w
        nodes.append(ResolvedNode(_nid("cm_head_box"), "box", Rect(x, y, cell_w, row_h),
                                  fill_color=palette.accent, group_id=gid))
        nodes.append(_make_text_node(_nid("cm_head"), opt, font, ts.body, bold=True,
                                     italic=False, rect=Rect(x, y, cell_w, row_h),
                                     color=palette.surface, group_id=gid))

    for r, crit in enumerate(slide.criteria):
        yy = y + (r + 1) * row_h
        gid = f"cm_crit_{r}"
        nodes.append(ResolvedNode(_nid("cm_crit_box"), "box", Rect(cx, yy, label_w, row_h),
                                  fill_color=palette.muted, group_id=gid))
        nodes.append(_make_text_node(_nid("cm_crit"), crit, font, ts.body, bold=True,
                                     italic=False, rect=Rect(cx, yy, label_w, row_h),
                                     color=palette.surface, group_id=gid))
        row = slide.cells[r] if r < len(slide.cells) else []
        for c in range(n_options):
            x = cx + label_w + c * cell_w
            cell = row[c] if c < len(row) else ""
            cg = f"cm_cell_{r}_{c}"
            nodes.append(ResolvedNode(_nid("cm_cell_box"), "box", Rect(x, yy, cell_w, row_h),
                                      fill_color="#F4F6F8", group_id=cg))
            nodes.append(_make_text_node(_nid("cm_cell"), cell, font, ts.body, bold=False,
                                         italic=False, rect=Rect(x, yy, cell_w, row_h),
                                         group_id=cg))
    return nodes


def _layout_team_grid(slide: TeamGridSlide, cx, cy, cw, ch, font, ts, palette):
    """People grid: each member gets a measured portrait tile, name, and role."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.members)
    cols = min(3, n) if n else 1
    rows = (n + cols - 1) // cols
    card_w = max(1, (cw - gap * (cols - 1)) // cols)
    card_h = max(1, (cy + ch - y - gap * (rows - 1)) // rows) if rows else cy + ch - y
    name_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    role_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
    inner = int(0.12 * EMU_PER_INCH)

    for i, member in enumerate(slide.members):
        r, c = divmod(i, cols)
        x = cx + c * (card_w + gap)
        yy = y + r * (card_h + gap)
        gid = f"team_{i}"
        portrait_h = max(1, card_h - name_h - role_h - 2 * inner)
        if member.image:
            nodes.append(ResolvedNode(_nid("team_img"), "image", Rect(x, yy, card_w, portrait_h),
                                      slot_type="image", text_content=member.image.path,
                                      group_id=gid))
        else:
            nodes.append(ResolvedNode(_nid("team_avatar"), "box", Rect(x, yy, card_w, portrait_h),
                                      fill_color=palette.muted, group_id=gid))
        nodes.append(_make_text_node(_nid("team_name"), member.name, font, ts.body, bold=True,
                                     italic=False, rect=Rect(x, yy + portrait_h + inner, card_w, name_h),
                                     color=palette.primary, group_id=gid))
        nodes.append(_make_text_node(_nid("team_role"), member.role, font, ts.caption, bold=False,
                                     italic=False,
                                     rect=Rect(x, yy + portrait_h + inner + name_h + inner, card_w, role_h),
                                     is_caption=True, color=palette.muted, group_id=gid))
    return nodes


def _layout_image_full_bleed(slide: ImageFullBleedSlide, cx, cy, cw, ch, font, ts, palette):
    """Full content-area image with optional lower-left overlay title."""
    nodes: list[ResolvedNode] = []
    gid = "image_full_bleed"
    nodes.append(ResolvedNode(_nid("full_image"), "image", Rect(cx, cy, cw, ch),
                              slot_type="image", text_content=slide.image.path,
                              group_id=gid))
    if slide.overlay_title:
        pad = int(0.25 * EMU_PER_INCH)
        box_w = int(cw * 0.62)
        text_w = box_w - 2 * pad
        title_lines = wrap(slide.overlay_title, font, ts.header, text_w, bold=True)
        title_h = max(1, total_text_height_emu(title_lines))
        box_h = title_h + 2 * pad
        box_x = cx + pad
        box_y = cy + ch - box_h - pad
        nodes.append(ResolvedNode(_nid("overlay_box"), "box", Rect(box_x, box_y, box_w, box_h),
                                  fill_color=palette.primary, group_id=gid))
        nodes.append(_make_text_node(_nid("overlay_title"), slide.overlay_title, font, ts.header,
                                     bold=True, italic=False,
                                     rect=Rect(box_x + pad, box_y + pad, text_w, title_h),
                                     lines=title_lines, color=palette.surface, group_id=gid))
    return nodes


def _layout_image_grid(slide: ImageGridSlide, cx, cy, cw, ch, font, ts, palette):
    """2–4 image gallery with optional captions below each measured image tile."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.images)
    cols = 2 if n <= 4 else 3
    rows = (n + cols - 1) // cols
    cell_w = max(1, (cw - gap * (cols - 1)) // cols)
    cell_h = max(1, (cy + ch - y - gap * (rows - 1)) // rows) if rows else cy + ch - y
    cap_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
    for i, img in enumerate(slide.images):
        r, c = divmod(i, cols)
        x = cx + c * (cell_w + gap)
        yy = y + r * (cell_h + gap)
        gid = f"imggrid_{i}"
        has_caption = i < len(slide.captions) and bool(slide.captions[i])
        img_h = cell_h - (cap_h + gap if has_caption else 0)
        nodes.append(ResolvedNode(_nid("grid_img"), "image", Rect(x, yy, cell_w, img_h),
                                  slot_type="image", text_content=img.path, group_id=gid))
        if has_caption:
            nodes.append(_make_text_node(_nid("grid_cap"), slide.captions[i], font, ts.caption,
                                         bold=False, italic=False,
                                         rect=Rect(x, yy + img_h + gap, cell_w, cap_h),
                                         is_caption=True, color=palette.muted, group_id=gid))
    return nodes


def _layout_logo_wall(slide: LogoWallSlide, cx, cy, cw, ch, font, ts, palette):
    """Partner/client logo wall: a restrained grid of labelled or image logo tiles."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    n = len(slide.logos)
    cols = min(4, n) if n else 1
    rows = (n + cols - 1) // cols
    cell_w = max(1, (cw - gap * (cols - 1)) // cols)
    cell_h = max(1, (cy + ch - y - gap * (rows - 1)) // rows) if rows else cy + ch - y
    for i, logo in enumerate(slide.logos):
        r, c = divmod(i, cols)
        x = cx + c * (cell_w + gap)
        yy = y + r * (cell_h + gap)
        gid = f"logo_{i}"
        nodes.append(ResolvedNode(_nid("logo_tile"), "box", Rect(x, yy, cell_w, cell_h),
                                  fill_color="#F4F6F8", group_id=gid))
        if logo.image:
            inset = int(0.18 * EMU_PER_INCH)
            nodes.append(ResolvedNode(_nid("logo_img"), "image",
                                      Rect(x + inset, yy + inset, cell_w - 2 * inset, cell_h - 2 * inset),
                                      slot_type="image", text_content=logo.image.path, group_id=gid))
        else:
            label = logo.label or "Logo"
            nodes.append(_make_text_node(_nid("logo_label"), label, font, ts.body, bold=True,
                                         italic=False, rect=Rect(x, yy, cell_w, cell_h),
                                         color=palette.primary, group_id=gid))
    return nodes


def _layout_content_list(slots, prefix: str, x, y, w, h, font, ts, palette=None) -> list[ResolvedNode]:
    """Lay out a flat list of content slots top-to-bottom within a rect.

    Uses GAP_MIN_EMU between items so the layout is consistent with the linter's
    E_GAP check. Heights are proportionally scaled to fit within the available h.
    """
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    cur_y = y

    # Pass 1 — compute intrinsic heights.
    fixed_heights: list[int] = []
    spacer_count = 0
    for slot in slots:
        if isinstance(slot, TextSlot):
            sz = slot.size_pt if slot.size_pt else ts.body
            lines = wrap(slot.content, font, sz, w, bold=slot.bold, italic=slot.italic)
            slot_h = total_text_height_emu(lines)
            if slot.max_lines:
                slot_h = min(slot_h, total_text_height_emu(lines[:slot.max_lines]))
            fixed_heights.append(max(1, slot_h))
        elif isinstance(slot, ImageSlot):
            fixed_heights.append(max(1, int(h * 0.6)))
        elif isinstance(slot, ChartSlot):
            fixed_heights.append(max(1, int(h * 0.7)))
        elif isinstance(slot, IconSlot):
            fixed_heights.append(max(1, int(0.5 * EMU_PER_INCH)))
        elif isinstance(slot, SpacerSlot):
            spacer_count += 1
            fixed_heights.append(0)

    n_fixed = sum(1 for fh in fixed_heights if fh > 0)
    n_gaps = max(0, len(slots) - 1)
    total_fixed = sum(fixed_heights)
    total_with_gaps = total_fixed + gap * n_gaps

    # Pass 1b — if total exceeds available height, scale heights proportionally.
    if total_with_gaps > h and total_fixed > 0:
        available_for_content = max(1, h - gap * n_gaps)
        scale = available_for_content / total_fixed
        fixed_heights = [max(1, int(fh * scale)) for fh in fixed_heights]
        total_fixed = sum(fixed_heights)

    spacer_h = max(0, (h - total_fixed - gap * n_gaps) // spacer_count) if spacer_count else 0

    for slot, fh in zip(slots, fixed_heights):
        if isinstance(slot, TextSlot):
            sz = slot.size_pt if slot.size_pt else ts.body
            lines = wrap(slot.content, font, sz, w, bold=slot.bold, italic=slot.italic)
            node = _make_text_node(_nid(f"{prefix}_text"), slot.content, font, sz,
                                   bold=slot.bold, italic=slot.italic,
                                   rect=Rect(x, cur_y, w, fh), lines=lines)
            nodes.append(node)
            cur_y += fh + gap
        elif isinstance(slot, ImageSlot):
            nodes.append(ResolvedNode(_nid(f"{prefix}_img"), "image",
                                      Rect(x, cur_y, w, fh),
                                      slot_type="image", text_content=slot.path))
            cur_y += fh + gap
        elif isinstance(slot, ChartSlot):
            nodes.append(ResolvedNode(_nid(f"{prefix}_chart"), "chart",
                                      Rect(x, cur_y, w, fh), slot_type="chart"))
            cur_y += fh + gap
        elif isinstance(slot, IconSlot):
            icon_size = fh
            nodes.append(ResolvedNode(_nid(f"{prefix}_icon"), "icon",
                                      Rect(x, cur_y, icon_size, icon_size),
                                      slot_type="icon", text_content=slot.name,
                                      fill_color=palette.accent if palette else None))
            cur_y += icon_size + gap
        elif isinstance(slot, SpacerSlot):
            if spacer_h > 0:
                cur_y += spacer_h + gap

    return nodes


# ── node factory ──────────────────────────────────────────────────────────────


def _make_text_node(
    node_id: str,
    text: str,
    font: str,
    size_pt: float,
    bold: bool,
    italic: bool,
    rect: Rect,
    lines: Optional[list] = None,
    is_chrome: bool = False,
    is_caption: bool = False,
    group_id: Optional[str] = None,
    color: Optional[str] = None,
    align: Optional[str] = None,
) -> ResolvedNode:
    if lines is None:
        lines = wrap(text, font, size_pt, rect.w, bold=bold, italic=italic)
    return ResolvedNode(
        node_id=node_id,
        node_type="text",
        rect=rect,
        lines=lines,
        font=font,
        size_pt=size_pt,
        bold=bold,
        italic=italic,
        text_content=text,
        is_chrome=is_chrome,
        is_caption=is_caption,
        group_id=group_id,
        text_color=color,
        align=align,
    )
