"""Two-pass flex layout engine.

Converts a DeckIR into a ResolvedDeck where every node has an absolute
EMU rect and every text node has its line boxes.

Pass 1 (measure): compute intrinsic/minimum sizes bottom-up.
Pass 2 (assign):  distribute available space top-down and record rects.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Optional

from slidekit.ir.models import (
    AgendaSlide,
    BeforeAfterSlide,
    BigNumberSlide,
    BulletListSlide,
    CardGridSlide,
    ChartSlide,
    ChartWithInsightSlide,
    ChecklistSlide,
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
    ProsConsSlide,
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
    TestimonialSlide,
    ThisVsThatSlide,
    TimelineSlide,
    TitleSlide,
    TwoColumnSlide,
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
from slidekit.metrics.measure import line_height_emu, measure_text, total_text_height_emu, wrap

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
    elif comp == "two-column":
        nodes = _layout_two_column(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
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
    elif comp == "checklist":
        nodes = _layout_checklist(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "numbered-steps":
        nodes = _layout_numbered_steps(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "before-after":
        nodes = _layout_before_after(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "pros-cons":
        nodes = _layout_pros_cons(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "this-vs-that":
        nodes = _layout_this_vs_that(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "kpi-grid":
        nodes = _layout_kpi_grid(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
    elif comp == "chart-slide":
        nodes = _layout_chart_slide(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
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
    elif comp == "testimonial":
        nodes = _layout_testimonial(slide, cx, cy, cw, ch_with_pn, font, ts, palette)
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
    )


# ── component layout functions ────────────────────────────────────────────────


def _layout_title_slide(slide: TitleSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = int(0.3 * EMU_PER_INCH)
    pad = int(0.5 * EMU_PER_INCH)

    # Title — vertically centered in upper 60% of content area.
    title_area_h = int(ch * 0.6)
    title_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
    title_y = cy + (title_area_h - title_h) // 2
    title_rect = Rect(cx + pad, title_y, cw - 2 * pad, title_h)
    nodes.append(
        _make_text_node(_nid("title"), slide.title, font, ts.title, bold=True,
                        italic=False, rect=title_rect, color=palette.primary)
    )

    if slide.subtitle:
        sub_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
        sub_y = title_y + title_h + gap
        sub_rect = Rect(cx + pad, sub_y, cw - 2 * pad, sub_h)
        nodes.append(
            _make_text_node(_nid("subtitle"), slide.subtitle, font, ts.body,
                            bold=False, italic=False, rect=sub_rect)
        )

    return nodes


def _layout_two_column(slide: TwoColumnSlide, cx, cy, cw, ch, font, ts, palette) -> list[ResolvedNode]:
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = cy

    if slide.title:
        title_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT * 1.2)
        title_rect = Rect(cx, y, cw, title_h)
        nodes.append(_make_text_node(_nid("title"), slide.title, font, ts.header,
                                     bold=True, italic=False, rect=title_rect,
                                     color=palette.primary))
        y += title_h + gap

    col_h = cy + ch - y
    total_w = cw - gap
    total_weight = slide.left_weight + slide.right_weight
    left_w = int(total_w * slide.left_weight / total_weight)
    right_w = total_w - left_w

    left_x = cx
    right_x = cx + left_w + gap

    left_node = _layout_content_list(slide.left, "left_col", left_x, y, left_w, col_h, font, ts, palette)
    right_node = _layout_content_list(slide.right, "right_col", right_x, y, right_w, col_h, font, ts, palette)
    nodes.extend(left_node)
    nodes.extend(right_node)
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
    icon_size = int(0.6 * EMU_PER_INCH)
    text_x = cx + icon_size + int(0.2 * EMU_PER_INCH)
    text_w = cw - icon_size - int(0.2 * EMU_PER_INCH)

    for row in slide.rows:
        icon_rect = Rect(cx, y + (row_h - icon_size) // 2, icon_size, icon_size)
        nodes.append(ResolvedNode(_nid("icon"), "icon", icon_rect,
                                  slot_type="icon", text_content=row.icon,
                                  fill_color=palette.accent))

        heading_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
        body_h = row_h - heading_h - gap
        nodes.append(_make_text_node(_nid("heading"), row.heading, font, ts.body,
                                     bold=True, italic=False,
                                     rect=Rect(text_x, y, text_w, heading_h)))
        nodes.append(_make_text_node(_nid("body"), row.body, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y + heading_h + gap, text_w, body_h)))
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

    for i, stat in enumerate(slide.stats):
        sx = cx + i * (stat_w + gap)
        value_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
        label_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
        sub_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT) if stat.subtext else 0

        inner_y = y + (stat_h - value_h - label_h - sub_h - gap * 2) // 2
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
                                         rect=Rect(sx, inner_y + value_h + label_h + gap * 2, stat_w, sub_h),
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

    icon_size = int(0.5 * EMU_PER_INCH)
    inner_gap = int(0.15 * EMU_PER_INCH)

    for i, card in enumerate(slide.cards):
        row_i = i // cols
        col_i = i % cols
        card_x = cx + col_i * (card_w + gap)
        card_y = y + row_i * (card_h + gap)
        gid = f"card_{i}"

        inner_y = card_y
        if card.icon:
            icon_rect = Rect(card_x, inner_y, icon_size, icon_size)
            nodes.append(ResolvedNode(_nid("card_icon"), "icon", icon_rect,
                                      slot_type="icon", text_content=card.icon,
                                      group_id=gid, fill_color=palette.accent))
            inner_y += icon_size + inner_gap

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


def _emphasis_stack(items, cx, cy, cw, ch, font, palette, *, bar=True):
    """Lay out a vertically-centred stack of text rows with an optional left
    accent bar. ``items`` is a list of dicts: prefix/text/size, optional
    bold/italic/is_caption/color. Returns a list of ResolvedNodes."""
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
    return _emphasis_stack([
        {"prefix": "sec_num", "text": slide.number, "size": ts.title, "bold": True,
         "color": palette.accent},
        {"prefix": "sec_title", "text": slide.title, "size": ts.header, "bold": True},
    ], cx, cy, cw, ch, font, palette)


def _layout_quote_opener(slide: QuoteOpenerSlide, cx, cy, cw, ch, font, ts, palette):
    return _emphasis_stack([
        {"prefix": "quote", "text": f'"{slide.quote}"', "size": ts.header,
         "bold": False, "italic": True},
        {"prefix": "attrib", "text": f"- {slide.attribution}", "size": ts.body,
         "bold": False, "color": palette.muted},
    ], cx, cy, cw, ch, font, palette)


def _layout_big_number(slide: BigNumberSlide, cx, cy, cw, ch, font, ts, palette):
    items = [
        {"prefix": "value", "text": slide.value, "size": ts.title, "bold": True,
         "color": palette.accent},
        {"prefix": "label", "text": slide.label, "size": ts.header, "bold": False},
    ]
    if slide.context:
        items.append({"prefix": "context", "text": slide.context, "size": ts.body,
                      "bold": False, "color": palette.muted})
    return _emphasis_stack(items, cx, cy, cw, ch, font, palette)


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


def _layout_bullet_list(slide: BulletListSlide, cx, cy, cw, ch, font, ts, palette):
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    title_node, y = _list_title(slide.title, cx, cy, cw, font, ts)
    nodes.append(title_node)

    n = len(slide.items)
    avail = cy + ch - y
    slot_h = max(1, (avail - gap * max(0, n - 1)) // n)
    item_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    marker = int(0.18 * EMU_PER_INCH)
    text_x = cx + int(0.5 * EMU_PER_INCH)
    text_w = cw - int(0.5 * EMU_PER_INCH)
    for i, item in enumerate(slide.items):
        gid = f"bullet_{i}"
        my = y + (item_h - marker) // 2
        nodes.append(ResolvedNode(_nid("bullet"), "box", Rect(cx, my, marker, marker),
                                  fill_color=palette.accent, group_id=gid))
        nodes.append(_make_text_node(_nid("bl_item"), item, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y, text_w, item_h), group_id=gid))
        y += slot_h + gap
    return nodes


def _layout_checklist(slide: ChecklistSlide, cx, cy, cw, ch, font, ts, palette):
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    title_node, y = _list_title(slide.title, cx, cy, cw, font, ts)
    nodes.append(title_node)

    n = len(slide.items)
    avail = cy + ch - y
    slot_h = max(1, (avail - gap * max(0, n - 1)) // n)
    item_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    box = int(0.32 * EMU_PER_INCH)
    text_x = cx + int(0.6 * EMU_PER_INCH)
    text_w = cw - int(0.6 * EMU_PER_INCH)
    for i, item in enumerate(slide.items):
        gid = f"check_{i}"
        by = y + (item_h - box) // 2
        # Filled accent box = checked; muted box = not yet done. Deterministic,
        # measurable — no glyph checkmarks.
        fill = palette.accent if item.checked else palette.muted
        nodes.append(ResolvedNode(_nid("check_box"), "box", Rect(cx, by, box, box),
                                  fill_color=fill, group_id=gid))
        nodes.append(_make_text_node(_nid("check_item"), item.text, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, y, text_w, item_h), group_id=gid))
        y += slot_h + gap
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
    icon = int(0.6 * EMU_PER_INCH)
    text_x = cx + icon + int(0.25 * EMU_PER_INCH)
    text_w = cw - icon - int(0.25 * EMU_PER_INCH)
    heading_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    inner = int(0.1 * EMU_PER_INCH)
    for i, feat in enumerate(slide.features):
        gid = f"feat_{i}"
        nodes.append(ResolvedNode(_nid("feat_icon"), "icon", Rect(cx, y, icon, icon),
                                  slot_type="icon", text_content=feat.icon, group_id=gid))
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


def _panel_items(nodes, items, x, y, w, h, font, ts, marker_color, prefix):
    """Render a bulleted column of items with square box markers (no glyph bullets).

    Each marker+text pair shares a group_id so the intentional marker-on-text row is
    exempt from E_GAP/E_OVERLAP while the linter still proves each row fits."""
    gap = GAP_MIN_EMU
    n = len(items)
    slot_h = max(1, (h - gap * max(0, n - 1)) // n)
    line_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    marker = int(0.18 * EMU_PER_INCH)
    text_x = x + int(0.4 * EMU_PER_INCH)
    text_w = w - int(0.4 * EMU_PER_INCH)
    cur = y
    for i, item in enumerate(items):
        gid = f"{prefix}_{i}"
        # Size each item box to its wrapped height (column is narrow → items may
        # wrap), capped at the slot so consecutive rows never collide.
        lines = wrap(item, font, ts.body, text_w)
        item_h = min(slot_h, max(line_h, total_text_height_emu(lines)))
        my = cur + (line_h - marker) // 2
        nodes.append(ResolvedNode(_nid(f"{prefix}_mark"), "box", Rect(x, my, marker, marker),
                                  fill_color=marker_color, group_id=gid))
        nodes.append(_make_text_node(_nid(f"{prefix}_item"), item, font, ts.body,
                                     bold=False, italic=False,
                                     rect=Rect(text_x, cur, text_w, item_h), lines=lines,
                                     group_id=gid))
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
    nodes.append(_make_text_node(_nid("lp_head"), left_head, font, ts.body, bold=True,
                                 italic=False, rect=Rect(cx, y, col_w, head_h),
                                 color=left_color))
    nodes.append(_make_text_node(_nid("rp_head"), right_head, font, ts.body, bold=True,
                                 italic=False, rect=Rect(right_x, y, col_w, head_h),
                                 color=right_color))
    items_y = y + head_h + gap
    items_h = cy + ch - items_y
    _panel_items(nodes, left_items, cx, items_y, col_w, items_h, font, ts, left_color, "lp")
    _panel_items(nodes, right_items, right_x, items_y, col_w, items_h, font, ts, right_color, "rp")
    return nodes


def _layout_before_after(slide: BeforeAfterSlide, cx, cy, cw, ch, font, ts, palette):
    """Two states head-to-head: the 'before' panel muted, the 'after' panel accent —
    a deterministic before→after improvement read."""
    return _two_panel_list(
        slide.title,
        slide.before.title, slide.before.items, palette.muted,
        slide.after.title, slide.after.items, palette.accent,
        cx, cy, cw, ch, font, ts, palette,
    )


def _layout_pros_cons(slide: ProsConsSlide, cx, cy, cw, ch, font, ts, palette):
    """Pros (accent) vs cons (muted), each a bulleted column."""
    return _two_panel_list(
        slide.title,
        slide.pros_title, slide.pros, palette.accent,
        slide.cons_title, slide.cons, palette.muted,
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

    badge = int(0.9 * EMU_PER_INCH)
    col_w = (cw - badge - 2 * gap) // 2
    left_x = cx
    right_x = cx + col_w + gap + badge + gap
    content_h = cy + ch - y

    value_h = int(ts.title * LINE_SPACING_SINGLE * EMU_PER_PT)
    label_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    block_h = value_h + gap + label_h
    inner_y = y + max(0, (content_h - block_h) // 2)

    for px, side, color in ((left_x, slide.left, palette.accent),
                            (right_x, slide.right, palette.primary)):
        nodes.append(_make_text_node(_nid("vs_value"), side.value, font, ts.title, bold=True,
                                     italic=False, rect=Rect(px, inner_y, col_w, value_h),
                                     color=color))
        nodes.append(_make_text_node(_nid("vs_label"), side.label, font, ts.body, bold=False,
                                     italic=False,
                                     rect=Rect(px, inner_y + value_h + gap, col_w, label_h)))

    # Central VS badge, vertically centred on the value line.
    badge_x = cx + (cw - badge) // 2
    badge_y = inner_y + max(0, (value_h - badge) // 2)
    nodes.append(ResolvedNode(_nid("vs_badge"), "box", Rect(badge_x, badge_y, badge, badge),
                              fill_color=palette.accent, group_id="vs_badge"))
    nodes.append(_make_text_node(_nid("vs_text"), "VS", font, ts.body, bold=True,
                                 italic=False, rect=Rect(badge_x, badge_y, badge, badge),
                                 group_id="vs_badge", color=palette.surface))
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

    value_h = int(ts.header * LINE_SPACING_SINGLE * EMU_PER_PT)
    rule_h = int(0.06 * EMU_PER_INCH)
    for i, kpi in enumerate(slide.kpis):
        gid = f"kpi_{i}"
        r, c = divmod(i, cols)
        kx = cx + c * (cell_w + gap)
        ky = y + r * (cell_h + gap)
        # Size the label box to its measured wrapped height so it never overflows;
        # centre the value/rule/label block within the cell.
        label_lines = wrap(kpi.label, font, ts.body, cell_w)
        label_h = max(1, total_text_height_emu(label_lines))
        block_h = value_h + gap + rule_h + gap + label_h
        inner_y = ky + max(0, (cell_h - block_h) // 2)
        nodes.append(_make_text_node(_nid("kpi_val"), kpi.value, font, ts.header, bold=True,
                                     italic=False, rect=Rect(kx, inner_y, cell_w, value_h),
                                     color=palette.accent, group_id=gid))
        ry = inner_y + value_h + gap
        nodes.append(ResolvedNode(_nid("kpi_rule"), "box",
                                  Rect(kx, ry, max(1, int(cell_w * 0.4)), rule_h),
                                  fill_color=palette.accent, group_id=gid))
        ly = ry + rule_h + gap
        nodes.append(_make_text_node(_nid("kpi_label"), kpi.label, font, ts.body, bold=False,
                                     italic=False, rect=Rect(kx, ly, cell_w, label_h),
                                     lines=label_lines, group_id=gid))
    return nodes


def _layout_chart_slide(slide: ChartSlide, cx, cy, cw, ch, font, ts, palette):
    """One captioned chart filling the content area below the title."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    y = _slide_title(nodes, slide.title, cx, cy, cw, font, ts, palette)

    caption_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT) if slide.caption else 0
    chart_h = cy + ch - y - (caption_h + gap if slide.caption else 0)
    nodes.extend(_chart_nodes(slide.chart, cx, y, cw, chart_h, font, ts, palette, "chart"))
    if slide.caption:
        nodes.append(_make_text_node(_nid("caption"), slide.caption, font, ts.caption,
                                     bold=False, italic=False,
                                     rect=Rect(cx, cy + ch - caption_h, cw, caption_h),
                                     is_caption=True, color=palette.muted))
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
    for idx, (head, items, color, qx, qy) in enumerate(quads):
        nodes.append(_make_text_node(_nid("swot_head"), head, font, ts.body, bold=True,
                                     italic=False, rect=Rect(qx, qy, col_w, head_h),
                                     color=color))
        items_y = qy + head_h + gap
        items_h = qy + cell_h - items_y
        _panel_items(nodes, items, qx, items_y, col_w, items_h, font, ts, color, f"swot{idx}")
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


def _layout_testimonial(slide: TestimonialSlide, cx, cy, cw, ch, font, ts, palette):
    """Customer quote with optional portrait, attribution, and accent quote bar."""
    nodes: list[ResolvedNode] = []
    gap = GAP_MIN_EMU
    portrait_w = int(cw * 0.28) if slide.image else 0
    quote_x = cx + (portrait_w + gap if slide.image else 0)
    quote_w = cw - (portrait_w + gap if slide.image else 0)
    gid = "testimonial"

    if slide.image:
        nodes.append(ResolvedNode(_nid("test_img"), "image", Rect(cx, cy, portrait_w, ch),
                                  slot_type="image", text_content=slide.image.path,
                                  group_id=gid))
    bar_w = int(0.10 * EMU_PER_INCH)
    nodes.append(ResolvedNode(_nid("test_bar"), "box", Rect(quote_x, cy, bar_w, ch),
                              fill_color=palette.accent, group_id=gid))
    text_x = quote_x + bar_w + int(0.25 * EMU_PER_INCH)
    text_w = quote_w - bar_w - int(0.25 * EMU_PER_INCH)
    quote_lines = wrap(f'"{slide.quote}"', font, ts.header, text_w, italic=True)
    quote_h = total_text_height_emu(quote_lines)
    name_h = int(ts.body * LINE_SPACING_SINGLE * EMU_PER_PT)
    role_h = int(ts.caption * LINE_SPACING_SINGLE * EMU_PER_PT)
    block_h = quote_h + gap + name_h + role_h
    y = cy + max(0, (ch - block_h) // 2)
    nodes.append(_make_text_node(_nid("test_quote"), f'"{slide.quote}"', font, ts.header,
                                 bold=False, italic=True, rect=Rect(text_x, y, text_w, quote_h),
                                 lines=quote_lines, group_id=gid))
    nodes.append(_make_text_node(_nid("test_name"), slide.name, font, ts.body, bold=True,
                                 italic=False, rect=Rect(text_x, y + quote_h + gap, text_w, name_h),
                                 color=palette.primary, group_id=gid))
    nodes.append(_make_text_node(_nid("test_role"), slide.role, font, ts.caption, bold=False,
                                 italic=False, rect=Rect(text_x, y + quote_h + gap + name_h, text_w, role_h),
                                 is_caption=True, color=palette.muted, group_id=gid))
    return nodes


# ── content list layout helper ────────────────────────────────────────────────


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
    )
