import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    return go, mo, pd


@app.cell
def _(mo):
    mo.md("""
    # RFC-8 Delphi Dashboard
    """)
    return


@app.cell
def _(mo):
    # Structure-only placeholder. Will become the real respondent list.
    respondent_options = ["Other - Josh", "Other - Juan Nunez-Iglesias", "GerBI (Damien)", "Fideus"]

    respondents_line = mo.md(f"**Respondents:** {', '.join(respondent_options)}")
    return (respondents_line,)


@app.cell
def _(go, mo):
    # Structure-only placeholder values.
    summary_pie = go.Figure(go.Pie(labels=["Under threshold", "Over threshold"], values=[12, 24], hole=0.4))
    summary_pie.update_layout(
        title="Threshold: 70",
        height=250,
        margin={"t": 40, "b": 10, "l": 10, "r": 10},
    )

    summary_text = mo.md(
        """
        **Overall proposal**: 65.2

        **Categories**
        - Building Blocks: 68.1
        - Abstract Concepts: 70.4
        - Core Classes: 63.8
        - User Stories: 85.2
        - Auxiliary: 66.7
        """
    )

    summary_card = mo.vstack([mo.md("### Summary"), summary_text, mo.ui.plotly(summary_pie)])
    return (summary_card,)


@app.cell
def _(mo, pd):
    # Structure-only placeholder rows.
    lowest5_metric = mo.ui.radio(options=["Average", "Median", "Min"], value="Average", label="Rank by")

    lowest5_dummy = pd.DataFrame(
        {
            "Section": [
                "P16: HCS",
                "P4: Consolidated Metadata",
                "P34: Compatibility",
                "P17: Core Class Changes Covered",
                "P35: Security",
            ],
            "Rating": [42, 44, 46, 53, 54],
        }
    )

    lowest5_card = mo.vstack([mo.md("### Lowest 5"), lowest5_metric, mo.ui.table(lowest5_dummy, selection=None)])
    return (lowest5_card,)


@app.cell
def _(mo, pd):
    # Structure-only placeholder rows.
    controversial5_dummy = pd.DataFrame(
        {
            "Section": [
                "P7: Attributes",
                "P17: Core Class Changes Covered",
                "P25: Rendering Settings",
                "P8: Metadata Storage",
                "P32: Prior Art",
            ],
            "Avg. Rating": [59, 53, 77, 68, 73],
            "Range": [75, 75, 70, 70, 70],
        }
    )

    controversial5_card = mo.vstack([mo.md("### Controversial 5"), mo.ui.table(controversial5_dummy, selection=None)])
    return (controversial5_card,)


@app.cell
def _(controversial5_card, lowest5_card, mo, summary_card):
    top_row = mo.hstack(
        [summary_card, lowest5_card, controversial5_card],
        justify="space-between",
        align="start",
        gap=1,
    )
    return (top_row,)


@app.cell
def _(go, mo):
    # Will become plot_ratings(df) from plotting.py.
    plot_placeholder_fig = go.Figure()
    plot_placeholder_fig.update_layout(
        height=500,
        annotations=[{"text": "Plot Ratings goes here", "showarrow": False, "font": {"size": 20}}],
    )
    plot_ratings_card = mo.vstack([mo.md("## Plot Ratings"), mo.ui.plotly(plot_placeholder_fig)])
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
