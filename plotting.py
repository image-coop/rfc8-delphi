import textwrap

import pandas as pd
import plotly.graph_objects as go
import seaborn as sns

from combine import (
    CATEGORY_ORDER,
    CATEGORY_TITLES,
    P_CATEGORIES,
    SECTION_SLUGS,
    get_numbers_only,
    get_text_feedback,
    melt_by_category,
    section_title,
)

SECTION_TITLES = {
    f"p{i}_{slug}": section_title(i, slug) for i, slug in enumerate(SECTION_SLUGS)
}

CATEGORY_COLORS = dict(
    zip(CATEGORY_ORDER, sns.color_palette("colorblind", n_colors=len(CATEGORY_ORDER)).as_hex())
)

BOX_FILL_OPACITY = 0.12
BOX_LINE_OPACITY = 0.35


def _rgba(hex_color, alpha):
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r}, {g}, {b}, {alpha})"


def get_plot_data(df):
    """
    One row per section x respondent rating, with that respondent's why/
    feedback text where they left any (NaN otherwise). Built by joining
    get_numbers_only's ratings with get_text_feedback's text.
    """
    long = melt_by_category(get_numbers_only(df)).dropna(subset=["rating"])
    text = get_text_feedback(df)

    return long.merge(
        text[["sec_name", "respondent", "why", "feedback"]],
        on=["sec_name", "respondent"],
        how="left",
    )


def _wrap_for_hover(text, width=60):
    lines = []
    for paragraph in str(text).splitlines():
        lines.extend(textwrap.wrap(paragraph, width=width) or [""])
    return "<br>".join(lines)


def _hover_text(label, rating, why, feedback):
    lines = [f"<b>{label}</b>", f"Rating: {rating:g}"]
    if pd.notna(why):
        lines.extend(["", "<b>Why</b>", _wrap_for_hover(why)])
    if pd.notna(feedback):
        lines.extend(["", "<b>What would increase support</b>", _wrap_for_hover(feedback)])
    return "<br>".join(lines)


def _anonymous_labels(plot_data):
    """Stable anonymous label ("Group 1", "Group 2", ...) per respondent id."""
    respondents = sorted(plot_data["respondent"].unique())
    return {r: f"Group {i + 1}" for i, r in enumerate(respondents)}


def _display_names(plot_data):
    """Human-readable name derived from each respondent id (e.g. "other_josh" -> "Other Josh")."""
    return {r: r.replace("_", " ").title() for r in plot_data["respondent"].unique()}


def build_ratings_figure(plot_data):
    """
    Horizontal box+strip plot: one box per section (median line + mean
    line via boxmean, quartile range) with every respondent's individual
    rating shown as a jittered point on top. Points are colored by the
    section's category (one trace per category, so the legend groups by
    category). Hovering a point shows a per-respondent label plus that
    respondent's rating and any why/feedback text; a toggle switches that
    label between an anonymous "Group N" tag (default) and the
    respondent's actual name. Buttons switch the section (y-axis) order
    between: ascending mean rating, descending mean rating, ascending
    minimum rating, and grouped by category (Overall, Building Blocks,
    Abstract Concepts, Core Classes, User Stories, Auxiliary -- top to
    bottom, same order as the legend).
    """
    anonymous_labels = _anonymous_labels(plot_data)
    display_names = _display_names(plot_data)
    rating_order_asc = (
        plot_data.groupby("sec_name")["rating"]
        .mean()
        .sort_values()
        .index.map(SECTION_TITLES)
        .tolist()
    )
    rating_order_desc = list(reversed(rating_order_asc))
    rating_order_min = (
        plot_data.groupby("sec_name")["rating"]
        .min()
        .sort_values()
        .index.map(SECTION_TITLES)
        .tolist()
    )
    category_order = [
        SECTION_TITLES[f"p{i}_{slug}"]
        for category in CATEGORY_ORDER
        for i, slug in enumerate(SECTION_SLUGS)
        if P_CATEGORIES[i] == category
    ]

    fig = go.Figure()
    anonymous_texts = []
    named_texts = []
    for category in CATEGORY_ORDER:
        sec_names = [
            f"p{i}_{slug}"
            for i, slug in enumerate(SECTION_SLUGS)
            if P_CATEGORIES[i] == category
        ]
        subset = plot_data[plot_data["sec_name"].isin(sec_names)]
        if subset.empty:
            continue

        anon_text = [
            _hover_text(anonymous_labels[r.respondent], r.rating, r.why, r.feedback)
            for r in subset.itertuples()
        ]
        named_text = [
            _hover_text(display_names[r.respondent], r.rating, r.why, r.feedback)
            for r in subset.itertuples()
        ]
        anonymous_texts.append(anon_text)
        named_texts.append(named_text)

        color = CATEGORY_COLORS[category]
        fig.add_trace(
            go.Box(
                x=subset["rating"],
                y=subset["sec_name"].map(SECTION_TITLES),
                name=CATEGORY_TITLES[category],
                boxpoints="all",
                jitter=0.4,
                pointpos=0,
                boxmean=True,
                orientation="h",
                text=anon_text,
                hovertemplate="%{text}<extra></extra>",
                hoveron="points",
                fillcolor=_rgba(color, BOX_FILL_OPACITY),
                line={"color": _rgba(color, BOX_LINE_OPACITY), "width": 1},
                marker={"color": color, "opacity": 0.85, "size": 6},
            )
        )

    fig.update_layout(
        title="RFC-8 Delphi ratings by section",
        xaxis_title="Rating",
        yaxis={
            "type": "category",
            "categoryorder": "array",
            "categoryarray": rating_order_asc,
            "autorange": "reversed",
        },
        boxmode="overlay",
        height=max(400, 28 * len(SECTION_SLUGS) + 150),
        legend_title_text="Category",
        legend={
            "itemclick": False,
            "itemdoubleclick": False,
            "x": 1.02,
            "xanchor": "left",
            "y": 1,
            "yanchor": "top",
        },
        updatemenus=[
            {
                "type": "buttons",
                "direction": "right",
                "x": 1,
                "xanchor": "right",
                "y": 1.08,
                "yanchor": "bottom",
                "buttons": [
                    {
                        "label": "Sort ascending",
                        "method": "relayout",
                        "args": [{"yaxis.categoryarray": rating_order_asc}],
                    },
                    {
                        "label": "Sort descending",
                        "method": "relayout",
                        "args": [{"yaxis.categoryarray": rating_order_desc}],
                    },
                    {
                        "label": "Sort by minimum",
                        "method": "relayout",
                        "args": [{"yaxis.categoryarray": rating_order_min}],
                    },
                    {
                        "label": "Group by category",
                        "method": "relayout",
                        "args": [{"yaxis.categoryarray": category_order}],
                    },
                ],
            },
            {
                "type": "buttons",
                "direction": "down",
                "x": 1.02,
                "xanchor": "left",
                "y": 0.8,
                "yanchor": "top",
                "active": 0,
                "buttons": [
                    {
                        "label": "Anonymous",
                        "method": "restyle",
                        "args": [{"text": anonymous_texts}],
                    },
                    {
                        "label": "Show names",
                        "method": "restyle",
                        "args": [{"text": named_texts}],
                    },
                ],
            },
        ],
    )
    return fig


def plot_ratings(df):
    """Convenience: build the ratings figure directly from a shortened, categorized df."""
    return build_ratings_figure(get_plot_data(df))
