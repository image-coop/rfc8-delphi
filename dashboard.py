# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo",
#     "pandas",
#     "plotly",
#     "seaborn",
# ]
# ///
import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    from utils.combine import (
        CATEGORY_ORDER,
        CATEGORY_OVERALL,
        CATEGORY_TITLES,
        LOW_RATING_THRESHOLD,
        get_numbers_only,
        get_text_feedback,
        get_top_level_feedback,
        prepare_df,
        section_stats,
    )
    from utils.plotting import SECTION_TITLES, plot_ratings

    return (
        CATEGORY_ORDER,
        CATEGORY_OVERALL,
        CATEGORY_TITLES,
        LOW_RATING_THRESHOLD,
        SECTION_TITLES,
        get_numbers_only,
        get_text_feedback,
        get_top_level_feedback,
        go,
        mo,
        pd,
        plot_ratings,
        prepare_df,
        section_stats,
    )


@app.cell
def _(mo, pd, prepare_df):
    DATA_PATH = mo.cli_args().get("csv-path")
    if not DATA_PATH:
        raise ValueError(
            "csv-path is required, e.g. "
            "marimo edit --sandbox dashboard.py -- -csv-path path/to/csv"
        )

    raw_df = pd.read_csv(DATA_PATH)
    df = prepare_df(raw_df)
    return (df,)


@app.cell
def _(df, section_stats):
    stats = section_stats(df)
    return (stats,)


@app.cell
def _(mo):
    mo.md("""
    # RFC-8 Delphi Dashboard
    """)
    return


@app.cell
def _(get_numbers_only, df, mo):
    respondent_ids = sorted(
        c
        for c in get_numbers_only(df).columns
        if c not in ("sec_name", "category", "average", "median")
    )
    respondents_line = mo.md(f"**Respondents:** {', '.join(respondent_ids)}")
    return (respondents_line,)


@app.cell
def _(
    CATEGORY_ORDER,
    CATEGORY_OVERALL,
    CATEGORY_TITLES,
    LOW_RATING_THRESHOLD,
    go,
    mo,
    stats,
):
    below_threshold = int((stats["mean"] < LOW_RATING_THRESHOLD).sum())
    at_or_above_threshold = int((stats["mean"] >= LOW_RATING_THRESHOLD).sum())

    summary_pie = go.Figure(
        go.Pie(
            labels=["Under threshold", "At/above threshold"],
            values=[below_threshold, at_or_above_threshold],
            hole=0.4,
        )
    )
    summary_pie.update_layout(
        title=f"Avg. Section Ratings Above and Below {LOW_RATING_THRESHOLD:g}",
        height=250,
        margin={"t": 40, "b": 10, "l": 10, "r": 10},
    )

    p0_avg = stats.loc[stats["sec_name"] == "p0_overall_proposal", "mean"].iloc[0]
    category_avgs = stats.groupby("category")["mean"].mean()
    category_lines = "\n".join(
        f"- **{CATEGORY_TITLES[category]}**: {category_avgs[category]:.1f}"
        for category in CATEGORY_ORDER
        if category != CATEGORY_OVERALL
    )

    summary_text = mo.md(f"""
Average ratings across respondents and sections by category:

- **Overall proposal**: {p0_avg:.1f}
{category_lines}
""")

    summary_card = mo.vstack(
        [mo.md("### Summary"), summary_text, mo.ui.plotly(summary_pie)]
    )
    return (summary_card,)


@app.cell
def _(mo):
    lowest5_metric = mo.ui.radio(
        options=["Average", "Median", "Min"], value="Average", label="Rank by"
    )
    return (lowest5_metric,)


@app.cell
def _(SECTION_TITLES, lowest5_metric, mo, stats):
    lowest5_description = mo.md(
        "Lowest ranked sections. Ranked by average or median across all groups"
        "or minimum individual rating received."
    )
    lowest5_metric_col = {"Average": "mean", "Median": "median", "Min": "min"}[
        lowest5_metric.value
    ]

    lowest5_df = stats.sort_values(lowest5_metric_col).head(5)[
        ["sec_name", lowest5_metric_col]
    ]
    lowest5_df = lowest5_df.rename(
        columns={"sec_name": "Section", lowest5_metric_col: "Rating"}
    )
    lowest5_df["Section"] = lowest5_df["Section"].map(SECTION_TITLES)

    lowest5_table = mo.ui.table(
        lowest5_df.to_dict("records"),
        selection=None,
        format_mapping={"Rating": lambda v: f"{v:.1f}"},
    )
    lowest5_card = mo.vstack(
        [mo.md("### Lowest 5"), lowest5_description, lowest5_metric, lowest5_table]
    )
    return (lowest5_card,)


@app.cell
def _(SECTION_TITLES, mo, stats):
    controversial5_description = mo.md(
        "Most controversial sections. Ranked by range of ratings across all groups."
    )
    controversial5_df = stats.sort_values("range", ascending=False).head(5)[
        ["sec_name", "mean", "range"]
    ]
    controversial5_df = controversial5_df.rename(
        columns={"sec_name": "Section", "mean": "Avg. Rating", "range": "Range"}
    )
    controversial5_df["Section"] = controversial5_df["Section"].map(SECTION_TITLES)

    controversial5_table = mo.ui.table(
        controversial5_df.to_dict("records"),
        selection=None,
        format_mapping={"Avg. Rating": lambda v: f"{v:.1f}"},
    )
    controversial5_card = mo.vstack(
        [mo.md("### Controversial 5"), controversial5_description, controversial5_table]
    )
    return (controversial5_card,)


@app.cell
def _(controversial5_card, lowest5_card, mo, summary_card):
    top_row = mo.hstack(
        [summary_card, lowest5_card, controversial5_card],
        justify="space-between",
        align="start",
        widths="equal",
        gap=1,
    )
    return (top_row,)


@app.cell
def _(df, mo, plot_ratings):
    plot_ratings_card = mo.vstack(
        [mo.md("## Plot Ratings"), mo.ui.plotly(plot_ratings(df))]
    )
    return (plot_ratings_card,)


@app.cell
def _(CATEGORY_TITLES, SECTION_TITLES, df, get_text_feedback, mo):
    feedback_df = get_text_feedback(df)[
        ["respondent", "sec_name", "category", "why", "feedback"]
    ].copy()
    feedback_df["category"] = feedback_df["category"].map(CATEGORY_TITLES)
    feedback_df["sec_name"] = feedback_df["sec_name"].map(SECTION_TITLES)
    feedback_df = feedback_df.rename(
        columns={
            "respondent": "Respondent",
            "sec_name": "Section",
            "category": "Category",
            "why": "Why",
            "feedback": "What would increase support?",
        }
    ).fillna("")

    feedback_table = mo.ui.table(
        feedback_df.to_dict("records"),
        selection=None,
        wrapped_columns=["Why", "What would increase support?"],
    )
    feedback_card = mo.vstack([mo.md("## Text Feedback"), feedback_table])
    return (feedback_card,)


@app.cell
def _(df, get_top_level_feedback, mo):
    top_level_df = (
        get_top_level_feedback(df)
        .rename(
            columns={
                "respondent": "Respondent",
                "top_changes": "Top Changes",
                "discussion_needed": "Discussion Needed",
            }
        )
        .fillna("")
    )

    top_level_table = mo.ui.table(
        top_level_df.to_dict("records"),
        selection=None,
        wrapped_columns=["Top Changes", "Discussion Needed"],
    )
    top_level_card = mo.vstack(
        [mo.md("## Top Changes / Discussion Needed"), top_level_table]
    )
    return (top_level_card,)


@app.cell
def _(
    feedback_card,
    mo,
    plot_ratings_card,
    respondents_line,
    top_level_card,
    top_row,
):
    mo.vstack(
        [respondents_line, top_row, plot_ratings_card, feedback_card, top_level_card],
        gap=2,
    )
    return


if __name__ == "__main__":
    app.run()
