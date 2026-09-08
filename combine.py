import re

import pandas as pd

PREFIX_NAMES = [
    "timestamp",
    "group",
    "name",
]

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


def shorten_column_names(df):
    new_columns = PREFIX_NAMES.copy()
    for i, slug in enumerate(SECTION_SLUGS):
        new_columns.extend([f"p{i}_{slug}", f"p{i}_why", f"p{i}_feedback"])
    new_columns.extend(SUFFIX_NAMES)

    if len(new_columns) != len(df.columns):
        raise ValueError(
            f"Expected {len(new_columns)} columns, got {len(df.columns)}"
        )

    df = df.copy()
    df.columns = new_columns
    return df

def categorize_ps(df):
    """
    Categorize the columns of the dataframe into broader headings.
    """
    df = df.copy()
    for i, category in P_CATEGORIES.items():
        df[f"p{i}_category"] = category
    return df

def _slugify(text):
    text = re.sub(r"[^a-z0-9]+", "_", str(text).strip().lower())
    return text.strip("_")


def _is_blank(value):
    return pd.isna(value) or not str(value).strip()


def _respondent_ids(df):
    ids = [
        f"{_slugify(group)}_{_slugify(name)}"
        for group, name in zip(df["group"], df["name"])
    ]
    if len(ids) != len(set(ids)):
        seen = set()
        dupes = {r for r in ids if r in seen or seen.add(r)}
        raise ValueError(f"Duplicate group/name combos: {sorted(dupes)}")
    return ids


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


def render_feedback_markdown(text_df, low_rating_threshold=LOW_RATING_THRESHOLD):
    """
    Render a get_text_feedback spreadsheet into a markdown document.
    Sections are grouped by category (then P-order within category); why
    and feedback comments are pooled per section with no respondent names
    shown, sorted by rating ascending, with a separator between comments
    below LOW_RATING_THRESHOLD and comments at or above it. Any top-level
    (non-section) text columns with content are appended at the end.
    """
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

            block = [f"### {section_title(i, slug)}", ""]
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
    
