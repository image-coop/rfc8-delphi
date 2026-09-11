# RFC-8 Delphi Analysis

This repo contains code for wrangling, analysing and exploring Delphi responses
to [RFC-8 - Collections & Extensions](https://ngff.openmicroscopy.org/rfc/8/index.html).

RFC-8 is an essential piece of the roadmap to [OME-Zarr v1.0](https://forum.image.sc/t/our-proposed-roadmap-to-ome-zarr-1-0/121995). It proposes a schema for declaring
and discovering collections of related objects (images, labels, tables, etc.) in OME-Zarr, and a mechanism that would allow the community to define and discover
extensions to the core schema.

We (Image Coop, RFC-8 authors, other interested parties) are using a Delphi-style* consultation process on RFC-8 to help us understand where participating groups currently agree, where there are differences, and which parts of the proposal may need further work.

A Delphi process is a structured way of building consensus through several rounds of anonymous or group-based assessment, with each round informed by the results of the previous one. See https://en.wikipedia.org/wiki/Delphi_method for a short overview.

If you'd like to learn more about how we're using this process for RFC-8, reach out
to omezarr@image.coop

## Usage

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and clone this repo.

2. Place response CSVs in a resources/ folder in your cloned RFC8-Delphi repo.

3. Use `uvx marimo run --sandbox dashboard.py -- -csv-path path/to/csv` to load the summary dashboard.

4. Use `uv run render_markdown.py path/to/csv path/to/markdown` to render summary markdown of a single csv.

5. If you wish to explore the spreadsheet on your own, you may want to use the `prepare_df` utility function. From the repo root:

```python
import pandas as pd
# other useful utilities live in this file. Check docstrings.
from utils.combine import prepare_df

df = pd.read_csv('path/to/csv')
df = prepare_df(df)
```
