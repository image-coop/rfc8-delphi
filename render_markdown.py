  # /// script
  # requires-python = ">=3.10"
  # dependencies = [
  #     "pandas",
  # ]
  # ///
import pandas as pd

from utils.combine import get_numbers_only, get_text_feedback, melt_by_category, render_feedback_markdown, categorize_ps, shorten_column_names
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run render_markdown.py <path_to_csv> <path_to_md>")
        sys.exit(1)

    csv_pth = sys.argv[1]
    md_pth = sys.argv[2]

    df = pd.read_csv(csv_pth)
    df = categorize_ps(shorten_column_names(df))
    text_df = get_text_feedback(df)
    ratings_df = melt_by_category(get_numbers_only(df))

    rendered_feedback = render_feedback_markdown(text_df, ratings_df)
    with open(md_pth, "w") as f:
        f.write(rendered_feedback)
    print(f"Rendered feedback written to {md_pth}")
