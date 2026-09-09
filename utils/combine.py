import pandas as pd

SECTION_SLUGS = [
    "overall_proposal",
    "motivation_goals_non_goals",
    "paths",
    "references",
    "consolidated_metadata",
    "building_blocks_covered",
    "abstract_node_concept",
    "attributes",
    "metadata_storage",
    "structure_covered",
    "collection",
    "single_scale",
    "multiscales",
    "coordinates",
    "labels",
    "label_attributes",
    "hcs",
    "core_class_changes_covered",
    "extension_system",
    "visualize_multiple_images",
    "mn_segmentations",
    "shallow_copies_with_segs",
    "correlative_imaging",
    "hcs_plates",
    "image_archive",
    "rendering_settings",
    "grouping_remote_images",
    "other_datatypes",
    "gallery_grid_views",
    "user_stories_covered",
    "drawbacks",
    "abandoned_ideas",
    "prior_art",
    "performance",
    "compatibility",
    "security",
]

# Exact original CSV header text for each entry in SECTION_SLUGS, in the same
# order. Used to locate each section's rating column by content rather than
# position, so column order/reordering in the source spreadsheet doesn't
# matter. The why/feedback columns aren't matched by text (they're identical
# boilerplate for every section) -- they're taken as the two columns
# immediately following the matched rating column.
SECTION_TITLES_RAW = [
    "P0. Overall proposal",
    "P1. Motivation (“the Why”) / Goals / Non-goals",
    "P2. Paths (including the Zarr & JSON types)",
    "P3. References (including remote)",
    "P4. Relationship to consolidated metadata",
    "P5. All necessary building blocks have been covered.",
    "P6. Abstract node concept",
    "P7. Attributes (including the typing system)",
    "P8. Metadata storage (including inlining, etc.)",
    "P9. The components of the necessary structure have been covered.",
    "P10. Collection",
    "P11. Single scale",
    "P12. Multiscales",
    "P13. Coordinates",
    "P14. Labels",
    "P15. LabelAttributes",
    "P16. HCS",
    "P17. All necessary core class changes have been covered.",
    "P18. Extension system (including naming scheme & the definition of extension points, but not the actual list of them)",
    "P19. Visualize multiple images",
    "P20. m:n segmentations",
    "P21. Shallow copies of images with segmentations",
    "P22. Correlative imaging",
    "P23. HCS plates",
    "P24. Image Archive",
    "P25. Rendering settings",
    "P26. Grouping together remote images",
    "P27. Adding other datatypes to images",
    "P28. Gallery / grid views",
    "P29. All critical user stories have been covered.",
    "P30. Drawbacks",
    "P31. Abandoned ideas",
    "P32. Prior art",
    "P33. Performance",
    "P34. Compatibility",
    "P35. Security",
]

# Alternate/reworded header text seen in some spreadsheet revisions for a
# section already in SECTION_TITLES_RAW, mapped to that section's canonical
# index. A spreadsheet may contain the primary title, an alternate title, or
# (having been asked under both labels across form revisions) both -- in the
# last case the columns are coalesced per-respondent, primary first.
ALTERNATE_SECTION_TITLES = {
    "P14. All necessary core classes are present and updated.": 17,
}

# Raw CSV header text -> short column name, for the single (non-repeating)
# columns. Matched by content, wherever they appear in the source file.
FIXED_COLUMNS = {
    "Timestamp": "timestamp",
    "Which group are you responding on behalf of?": "group",
    "If other, please say which": "name",
    "What are the 1–3 most important changes that would increase your group’s support for RFC-8?": "top_changes",
    "Are there any propositions where your group believes further discussion is essential?": "discussion_needed",
}

SUFFIX_NAMES = [
    "top_changes",
    "discussion_needed",
]

CATEGORY_OVERALL = "overall"
CATEGORY_AUXILIARY = "auxiliary"
CATEGORY_BUILDING_BLOCKS = "building_blocks"
CATEGORY_ABSTRACT_CONCEPTS = "abstract_concepts"
CATEGORY_CORE_CLASSES = "core_classes"
CATEGORY_USER_STORIES = "user_stories"

P_CATEGORIES = {0: CATEGORY_OVERALL, 1: CATEGORY_AUXILIARY}
P_CATEGORIES.update({i: CATEGORY_BUILDING_BLOCKS for i in range(2, 6)})
P_CATEGORIES.update({i: CATEGORY_ABSTRACT_CONCEPTS for i in range(6, 10)})
P_CATEGORIES.update({i: CATEGORY_CORE_CLASSES for i in range(10, 19)})
P_CATEGORIES.update({i: CATEGORY_USER_STORIES for i in range(19, 30)})
P_CATEGORIES.update({i: CATEGORY_AUXILIARY for i in range(30, 36)})

CATEGORY_ORDER = [
    CATEGORY_OVERALL,
    CATEGORY_BUILDING_BLOCKS,
    CATEGORY_ABSTRACT_CONCEPTS,
    CATEGORY_CORE_CLASSES,
    CATEGORY_USER_STORIES,
    CATEGORY_AUXILIARY,
]

CATEGORY_TITLES = {
    CATEGORY_OVERALL: "Overall",
    CATEGORY_BUILDING_BLOCKS: "Building Blocks",
    CATEGORY_ABSTRACT_CONCEPTS: "Abstract Concepts",
    CATEGORY_CORE_CLASSES: "Core Classes",
    CATEGORY_USER_STORIES: "User Stories",
    CATEGORY_AUXILIARY: "Auxiliary",
}

LOW_RATING_THRESHOLD = 70


# Every known raw header text -> canonical section index. A section can have
# more than one raw text mapping to it (primary + alternates), so this isn't
# invertible; SECTION_TITLES_RAW remains the canonical index -> primary text
# direction.
SECTION_TITLE_TO_INDEX = {title: i for i, title in enumerate(SECTION_TITLES_RAW)}
SECTION_TITLE_TO_INDEX.update(ALTERNATE_SECTION_TITLES)


def _coalesce(df, indices):
    """Pick one of two possible columns for a section (support different spreadsheet versions)."""
    series = [df.iloc[:, i] for i in indices if i is not None]
    if not series:
        return float("nan")
    result = series[0]
    for s in series[1:]:
        result = result.combine_first(s)
    return result


def shorten_column_names(df):
    """
    Rename raw survey columns to short names by matching header text:
      - Timestamp/group/name/top_changes/discussion_needed are matched by
        exact text, wherever they appear.
      - Each section's rating column is matched by its exact title text --
        either the original wording in SECTION_TITLES_RAW, or a reworded
        variant registered in ALTERNATE_SECTION_TITLES to handle different
        spreadsheet formats.
        The two columns immediately following a matched title are taken as
        its why/feedback (those are identical boilerplate text for every
        section, so can't be matched by content).
      - A section not found at all in this spreadsheet gets NaN-filled
        rating/why/feedback columns instead of raising.
      - Any column that doesn't match anything known is dropped (with a
        warning).
    """
    columns = list(df.columns)
    used = [False] * len(columns)

    matched_fixed = {}
    for i, col in enumerate(columns):
        if col in FIXED_COLUMNS:
            matched_fixed[FIXED_COLUMNS[col]] = i
            used[i] = True

    matched_sections = {}
    for i, col in enumerate(columns):
        if used[i]:
            continue
        idx = SECTION_TITLE_TO_INDEX.get(col)
        if idx is None:
            continue
        used[i] = True
        why_idx = i + 1 if i + 1 < len(columns) and not used[i + 1] else None
        feedback_idx = i + 2 if i + 2 < len(columns) and not used[i + 2] else None
        if why_idx is not None:
            used[why_idx] = True
        if feedback_idx is not None:
            used[feedback_idx] = True
        matched_sections.setdefault(idx, []).append((i, why_idx, feedback_idx))

    missing_fixed = [name for name in FIXED_COLUMNS.values() if name not in matched_fixed]
    missing_sections = [i for i in range(len(SECTION_SLUGS)) if i not in matched_sections]
    if missing_fixed or missing_sections:
        raise ValueError(
            f"Missing expected columns: fixed={missing_fixed}, "
            f"sections={[SECTION_TITLES_RAW[i] for i in missing_sections]}"
        )

    dropped = [columns[i] for i in range(len(columns)) if not used[i]]
    if dropped:
        print(f"shorten_column_names: dropping unrecognized columns: {dropped}")

    out = {name: df.iloc[:, matched_fixed[name]] for name in ("timestamp", "group", "name")}

    for i, slug in enumerate(SECTION_SLUGS):
        matches = matched_sections[i]
        out[f"p{i}_{slug}"] = _coalesce(df, [m[0] for m in matches])
        out[f"p{i}_why"] = _coalesce(df, [m[1] for m in matches])
        out[f"p{i}_feedback"] = _coalesce(df, [m[2] for m in matches])

    for name in SUFFIX_NAMES:
        out[name] = df.iloc[:, matched_fixed[name]]

    return pd.DataFrame(out)

def categorize_ps(df):
    """
    Categorize the columns of the dataframe into broader headings.
    """
    df = df.copy()
    for i, category in P_CATEGORIES.items():
        df[f"p{i}_category"] = category
    return df


def prepare_df(raw_df):
    """
    The one required prep step for a raw survey export before any other
    function in this module (or plotting.py) can be used: shortens column
    names and adds p{i}_category columns.
    """
    return categorize_ps(shorten_column_names(raw_df))


def _is_blank(value):
    return pd.isna(value) or not str(value).strip()


def _respondent_ids(df):
    ids = [
        str(group).strip() if _is_blank(name) else f"{str(group).strip()} - {str(name).strip()}"
        for group, name in zip(df["group"], df["name"])
    ]
    if len(ids) != len(set(ids)):
        seen = set()
        dupes = {r for r in ids if r in seen or seen.add(r)}
        raise ValueError(f"Duplicate group/name combos: {sorted(dupes)}")
    return ids


def anonymize_respondents(df):
    """
    Return a copy of a shortened/categorized df with group/name replaced by
    generic labels ("Group 1", "Group 2", ...), assigned in a stable order
    (sorted by the existing respondent id) so re-running gives the same
    mapping. Apply this before get_numbers_only/get_text_feedback/
    get_plot_data if you want anonymous output -- those functions and
    plot_ratings always just display whatever's in group/name as-is.
    """
    ids = _respondent_ids(df)
    order = {respondent_id: i + 1 for i, respondent_id in enumerate(sorted(set(ids)))}

    df = df.copy()
    df["group"] = [f"Group {order[respondent_id]}" for respondent_id in ids]
    df["name"] = float("nan")
    return df


def get_numbers_only(df):
    """
    Reshape a shortened, categorized df so each row is a section (sec_name)
    with its category, and each respondent (group + name) gets a column
    holding the rating they gave that section.
    """
    respondent_ids = _respondent_ids(df)

    records = []
    for i, slug in enumerate(SECTION_SLUGS):
        sec_name = f"p{i}_{slug}"
        ratings = df[sec_name]
        record = {
            "sec_name": sec_name,
            "category": df[f"p{i}_category"].iloc[0],
        }
        record.update(zip(respondent_ids, ratings))
        record["average"] = ratings.mean()
        record["median"] = ratings.median()
        records.append(record)

    return pd.DataFrame(records)


def melt_by_category(numbers_df):
    respondent_cols = [
        c for c in numbers_df.columns
        if c not in ("sec_name", "category", "average", "median")
    ]

    long = numbers_df.melt(
        id_vars=["sec_name", "category"],
        value_vars=respondent_cols,
        var_name="respondent",
        value_name="rating",
    )

    return long


def long_ratings(df):
    """Every rating, one row per section x respondent. Shorthand for melt_by_category(get_numbers_only(df))."""
    return melt_by_category(get_numbers_only(df))


def section_stats(df, respondents=None):
    """
    Per-section rating stats (mean, median, min, max, range = max - min),
    optionally filtered to a subset of respondents.
    """
    ratings = long_ratings(df)
    if respondents is not None:
        ratings = ratings[ratings["respondent"].isin(respondents)]

    stats = (
        ratings.groupby(["sec_name", "category"])["rating"]
        .agg(mean="mean", median="median", min="min", max="max")
        .reset_index()
    )
    stats["range"] = stats["max"] - stats["min"]
    return stats


def get_text_feedback(df):
    """
    Long-format spreadsheet of free-text feedback: one row per question x respondent,
    with the respondent's rating (where applicable) plus their "why" and "feedback" text.
    
    Rows where every text field is blank are dropped.
    """
    respondent_ids = _respondent_ids(df)

    records = []
    for i, slug in enumerate(SECTION_SLUGS):
        sec_name = f"p{i}_{slug}"
        category = df[f"p{i}_category"].iloc[0]
        for respondent, rating, why, feedback in zip(
            respondent_ids, df[sec_name], df[f"p{i}_why"], df[f"p{i}_feedback"]
        ):
            why_blank = _is_blank(why)
            feedback_blank = _is_blank(feedback)
            if why_blank and feedback_blank:
                continue
            records.append({
                "sec_name": sec_name,
                "category": category,
                "respondent": respondent,
                "rating": rating,
                "why": None if why_blank else why,
                "feedback": None if feedback_blank else feedback,
            })

    for suffix_name in SUFFIX_NAMES:
        for respondent, text in zip(respondent_ids, df[suffix_name]):
            if _is_blank(text):
                continue
            records.append({
                "sec_name": suffix_name,
                "category": None,
                "respondent": respondent,
                "rating": None,
                "why": None,
                "feedback": text,
            })

    return pd.DataFrame(records)


def section_title(i, slug):
    return f"P{i}: {slug.replace('_', ' ').title()}"


def _suffix_title(suffix_name):
    return suffix_name.replace("_", " ").title()


def _format_rated_comments(rows, low_rating_threshold=LOW_RATING_THRESHOLD):
    """
    rows: list of (rating, text) tuples. Sorts by rating ascending and
    inserts a separator between comments below LOW_RATING_THRESHOLD and
    comments at or above it. Each comment is rendered as a blockquote with
    the rating bolded on its own line, so multi-paragraph responses stay
    grouped together instead of breaking out of a list item.
    """
    sorted_rows = sorted(rows, key=lambda r: r[0])
    lines = []
    separator_done = False
    for rating, text in sorted_rows:
        if not separator_done and rating >= low_rating_threshold:
            if lines:
                lines.append("---")
                lines.append("")
            separator_done = True
        lines.append(f"> **{rating:g}**")
        lines.append(">")
        for paragraph in str(text).splitlines():
            lines.append(f"> {paragraph}" if paragraph.strip() else ">")
        lines.append("")
    return lines


def render_feedback_markdown(df, low_rating_threshold=LOW_RATING_THRESHOLD):
    """
    Render a prepared df (see prepare_df) into a markdown feedback document.
    Sections are grouped by category (then P-order within category).
    Under each section's title, its average rating and every respondent's
    individual rating (by name) are listed, sorted alphabetically by
    respondent. Why and feedback comments are then pooled per section with
    no respondent names shown, sorted by rating ascending, with a separator
    between comments below LOW_RATING_THRESHOLD and comments at or above
    it. Any top-level (non-section) text columns with content are appended
    at the end.
    """
    text_df = get_text_feedback(df)
    ratings_df = long_ratings(df)

    lines = ["# RFC-8 Delphi Feedback", ""]

    for category in CATEGORY_ORDER:
        indices = [i for i in range(len(SECTION_SLUGS)) if P_CATEGORIES[i] == category]
        section_blocks = []
        for i in indices:
            slug = SECTION_SLUGS[i]
            sec_name = f"p{i}_{slug}"
            section_rows = text_df[text_df["sec_name"] == sec_name]
            if section_rows.empty:
                continue

            why_rows = [
                (row.rating, row.why)
                for row in section_rows.itertuples()
                if pd.notna(row.why)
            ]
            feedback_rows = [
                (row.rating, row.feedback)
                for row in section_rows.itertuples()
                if pd.notna(row.feedback)
            ]
            if not why_rows and not feedback_rows:
                continue

            section_ratings = (
                ratings_df[ratings_df["sec_name"] == sec_name]
                .dropna(subset=["rating"])
                .sort_values("respondent")
            )

            block = [f"### {section_title(i, slug)}", ""]
            if not section_ratings.empty:
                block.append(f"**Average rating:** {section_ratings['rating'].mean():.1f}")
                block.append("")
                block.extend(
                    f"- {row.respondent}: {row.rating:g}"
                    for row in section_ratings.itertuples()
                )
                block.append("")
            if why_rows:
                block.append("#### Why")
                block.append("")
                block.extend(_format_rated_comments(why_rows, low_rating_threshold=low_rating_threshold))
                block.append("")
            if feedback_rows:
                block.append("#### What would increase support")
                block.append("")
                block.extend(_format_rated_comments(feedback_rows, low_rating_threshold=low_rating_threshold))
                block.append("")
            section_blocks.append(block)

        if not section_blocks:
            continue

        lines.append(f"## {CATEGORY_TITLES[category]}")
        lines.append("")
        for block in section_blocks:
            lines.extend(block)

    extra_blocks = []
    for suffix_name in SUFFIX_NAMES:
        rows = text_df[text_df["sec_name"] == suffix_name]
        if rows.empty:
            continue
        block = [f"### {_suffix_title(suffix_name)}", ""]
        for text in rows["feedback"]:
            for paragraph in str(text).splitlines():
                block.append(f"> {paragraph}" if paragraph.strip() else ">")
            block.append("")
        extra_blocks.append(block)

    if extra_blocks:
        lines.append("## Additional Feedback")
        lines.append("")
        for block in extra_blocks:
            lines.extend(block)

    return "\n".join(lines).rstrip() + "\n"
    
