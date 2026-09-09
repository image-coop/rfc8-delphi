  # /// script
  # requires-python = ">=3.10"
  # dependencies = [
  #     "pandas",
  # ]
  # ///
import pandas as pd

from utils.combine import prepare_df, render_feedback_markdown
import sys

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: uv run render_markdown.py <path_to_csv> <path_to_md>")
        sys.exit(1)

    csv_pth = sys.argv[1]
    md_pth = sys.argv[2]

    df = prepare_df(pd.read_csv(csv_pth))
    rendered_feedback = render_feedback_markdown(df)
    with open(md_pth, "w") as f:
        f.write(rendered_feedback)
    print(f"Rendered feedback written to {md_pth}")
