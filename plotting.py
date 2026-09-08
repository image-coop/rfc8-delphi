import textwrap

import pandas as pd
import plotly.graph_objects as go

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


def _hover_text(rating, why, feedback):
    lines = [f"Rating: {rating:g}"]
    if pd.notna(why):
        lines.extend(["", "<b>Why</b>", _wrap_for_hover(why)])
    if pd.notna(feedback):
        lines.extend(["", "<b>What would increase support</b>", _wrap_for_hover(feedback)])
    return "<br>".join(lines)


def build_ratings_figure(plot_data):
    """
    Horizontal box+strip plot: one box per section (median line + mean
    line via boxmean, quartile range) with every respondent's individual
    rating shown as a jittered point on top. Points are colored by the
    section's category (one trace per category, so the legend groups by
    category). Hovering a point shows that respondent's rating and any
    why/feedback text, with no respondent identity shown. Buttons switch
    the section (y-axis) order between ascending rating, descending
    rating, and grouped by category (Overall, Building Blocks, Abstract
    Concepts, Core Classes, User Stories, Auxiliary -- top to bottom,
    same order as the legend).
    """
    rating_order_asc = (
        plot_data.groupby("sec_name")["rating"]
        .mean()
        .sort_values()
        .index.map(SECTION_TITLES)
        .tolist()
    )
    rating_order_desc = list(reversed(rating_order_asc))
    category_order = [
        SECTION_TITLES[f"p{i}_{slug}"]
        for category in CATEGORY_ORDER
        for i, slug in enumerate(SECTION_SLUGS)
        if P_CATEGORIES[i] == category
    ]

    fig = go.Figure()
    for category in CATEGORY_ORDER:
        sec_names = [
            f"p{i}_{slug}"
            for i, slug in enumerate(SECTION_SLUGS)
            if P_CATEGORIES[i] == category
        ]
        subset = plot_data[plot_data["sec_name"].isin(sec_names)]
        if subset.empty:
            continue

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
                text=[
                    _hover_text(r.rating, r.why, r.feedback)
                    for r in subset.itertuples()
                ],
                hovertemplate="%{text}<extra></extra>",
                hoveron="points",
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
                        "label": "Group by category",
                        "method": "relayout",
                        "args": [{"yaxis.categoryarray": category_order}],
                    },
                ],
            }
        ],
    )
    return fig


def plot_ratings(df):
    """Convenience: build the ratings figure directly from a shortened, categorized df."""
    return build_ratings_figure(get_plot_data(df))
