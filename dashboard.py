import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    from combine import (
        CATEGORY_ORDER,
        CATEGORY_OVERALL,
        CATEGORY_TITLES,
        LOW_RATING_THRESHOLD,
        categorize_ps,
        get_numbers_only,
        section_stats,
        shorten_column_names,
    )
    from plotting import SECTION_TITLES, plot_ratings

    return (
        CATEGORY_ORDER,
        CATEGORY_OVERALL,
        CATEGORY_TITLES,
        LOW_RATING_THRESHOLD,
        SECTION_TITLES,
        categorize_ps,
        get_numbers_only,
        go,
        mo,
        pd,
        plot_ratings,
        section_stats,
        shorten_column_names,
    )


@app.cell
def _(categorize_ps, pd, shorten_column_names):
    DATA_PATH = "resources/all_delphi_r1_v3.csv"

    raw_df = pd.read_csv(DATA_PATH)
    df = categorize_ps(shorten_column_names(raw_df))
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
        c for c in get_numbers_only(df).columns
        if c not in ("sec_name", "category", "average", "median")
    )
    respondents_line = mo.md(f"**Respondents:** {', '.join(respondent_ids)}")
    return (respondents_line,)


@app.cell
def _(CATEGORY_ORDER, CATEGORY_OVERALL, CATEGORY_TITLES, LOW_RATING_THRESHOLD, go, mo, stats):
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
"""
    )

    summary_card = mo.vstack([mo.md("### Summary"), summary_text, mo.ui.plotly(summary_pie)])
    return (summary_card,)


@app.cell
def _(mo):
    lowest5_metric = mo.ui.radio(options=["Average", "Median", "Min"], value="Average", label="Rank by")
    return (lowest5_metric,)


@app.cell
def _(SECTION_TITLES, lowest5_metric, mo, stats):

    lowest5_description = mo.md(
        "Lowest ranked sections. Ranked by average or median across all groups" \
        "or minimum individual rating received."
    )
    lowest5_metric_col = {"Average": "mean", "Median": "median", "Min": "min"}[lowest5_metric.value]

    lowest5_df = stats.sort_values(lowest5_metric_col).head(5)[["sec_name", lowest5_metric_col]]
    lowest5_df = lowest5_df.rename(columns={"sec_name": "Section", lowest5_metric_col: "Rating"})
    lowest5_df["Section"] = lowest5_df["Section"].map(SECTION_TITLES)

    lowest5_table = mo.ui.table(
        lowest5_df.to_dict("records"),
        selection=None,
        format_mapping={"Rating": lambda v: f"{v:.1f}"},
    )
    lowest5_card = mo.vstack([mo.md("### Lowest 5"), lowest5_description, lowest5_metric, lowest5_table])
    return (lowest5_card,)


@app.cell
def _(SECTION_TITLES, mo, stats):
    controversial5_df = stats.sort_values("range", ascending=False).head(5)[["sec_name", "mean", "range"]]
    controversial5_df = controversial5_df.rename(
        columns={"sec_name": "Section", "mean": "Avg. Rating", "range": "Range"}
    )
    controversial5_df["Section"] = controversial5_df["Section"].map(SECTION_TITLES)

    controversial5_table = mo.ui.table(
        controversial5_df.to_dict("records"),
        selection=None,
        format_mapping={"Avg. Rating": lambda v: f"{v:.1f}"},
    )
    controversial5_card = mo.vstack([mo.md("### Controversial 5"), controversial5_table])
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
    plot_ratings_card = mo.vstack([mo.md("## Plot Ratings"), mo.ui.plotly(plot_ratings(df))])
    return (plot_ratings_card,)


@app.cell
def _(mo, pd):
    # Will become get_text_feedback(df) from combine.py.
    feedback_dummy = pd.DataFrame(
        {
            "Respondent": ["Other - Josh", "GerBI (Damien)"],
            "Category": ["overall", "core_classes"],
            "Why": ["Placeholder why text...", "Another placeholder why..."],
            "What would increase support?": ["Lorem ipsum is a dummy or placeholder text commonly used in graphic design, publishing, and web development. It is typically a corrupted version of De finibus bonorum et malorum, a 1st-century BC text by the Roman statesman and philosopher Cicero, with words altered, added, and removed to make it nonsensical and improper Latin. The first two words are the truncation of dolorem ipsum. Lorem ipsum's purpose is to permit a page layout to be designed,"+
            "\n\n"+
            "independently of the copy that will subsequently populate it, or to demonstrate various fonts of a typeface without meaningful text", "More placeholder feedback..."],
        }
    )
    feedback_table = mo.ui.table(
        feedback_dummy,
        selection=None,
        wrapped_columns=["Why", "What would increase support?"],
    )
    feedback_card = mo.vstack([mo.md("## Text Feedback"), feedback_table])
    return (feedback_card,)


@app.cell
def _(feedback_card, mo, plot_ratings_card, respondents_line, top_row):
    mo.vstack([respondents_line, top_row, plot_ratings_card, feedback_card], gap=2)
    return


if __name__ == "__main__":
    app.run()
