# RFC-8 Delphi Analysis

This repo contains code for wrangling, analysing and exploring Delphi responses
to RFC-8.

## Usage

1. Place response CSVs in a resources/ folder in your cloned RFC8-Delphi repo.

2. Use `uvx marimo run --sandbox dashboard.py -- -csv-path path/to/csv` to load the summary dashboard.

3. Use `uv run render_markdown.py path/to/csv path/to/markdown` to render summary markdown of a single csv.

4. If you wish to explore the spreadsheet on your own, you may want to use the `prepare_df` utility function. From the repo root:

```python
import pandas as pd
# other useful utilities live in this file. Check docstrings.
from utils.combine import prepare_df

df = pd.read_csv('path/to/csv')
df = prepare_df(df)
```
