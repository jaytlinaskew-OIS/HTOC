"""
Gradio frontend for searching indicators by tags.

Run:
  py -m pip install gradio
  py gradio_search_indicators.py
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import gradio as gr
import pandas as pd

from search_indicators_by_tags import (
    AUTO_SAVED_SEARCH_FILES_DIR,
    DEFAULT_SCORES_EXCEL_PATH,
    DEFAULT_TAGS_FILE_PATH,
    _parse_terms,
    filter_scores_by_indicators_sorted,
    scan_tags_for_indicators_sorted,
    sort_scores_by_htoc_threat_desc,
)
DEFAULT_TAG_COLUMN = "tag"
DEFAULT_MATCH_MODE = "contains"
DEFAULT_MULTI_INPUT_MODE = "any"
DEFAULT_CASE_SENSITIVE = False
DEFAULT_CHUNKSIZE = 5000
DEFAULT_MAX_ROWS = 500
LOCAL_FALLBACK_SAVE_DIR = Path(__file__).resolve().parent / "saved_search_files"


def _load_available_tags(tags_file_path: Path, tag_column: str) -> list[str]:
    if not tags_file_path.exists():
        return []

    unique_tags: set[str] = set()
    try:
        for chunk in pd.read_csv(
            tags_file_path,
            dtype=str,
            usecols=[tag_column],
            chunksize=DEFAULT_CHUNKSIZE,
        ):
            values = (
                chunk[tag_column]
                .astype("string")
                .str.strip()
                .replace("", pd.NA)
                .dropna()
                .tolist()
            )
            unique_tags.update(values)
    except Exception:
        return []

    return sorted(unique_tags, key=lambda t: t.lower())


def _save_scores_csv(scores_df: pd.DataFrame, requested_name: str) -> Path:
    target_dir = (
        AUTO_SAVED_SEARCH_FILES_DIR
        if AUTO_SAVED_SEARCH_FILES_DIR.exists()
        else LOCAL_FALLBACK_SAVE_DIR
    )
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = requested_name.strip() if requested_name else ""
    if safe_name:
        safe_name = safe_name.replace("\\", "_").replace("/", "_")
        if not safe_name.lower().endswith(".csv"):
            safe_name += ".csv"
        filename = safe_name
    else:
        filename = f"threat_scores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    out_path = target_dir / filename
    scores_df.to_csv(out_path, index=False)
    return out_path


def run_search(
    search_terms: str,
    selected_tags: list[str] | None,
    save_to_csv: bool,
    output_csv_name: str,
) -> tuple[pd.DataFrame, pd.DataFrame, str, str]:
    try:
        manual_terms = _parse_terms(search_terms)
        selected_terms = [str(t).strip() for t in (selected_tags or []) if str(t).strip()]
        tag_terms: list[str] = []
        seen: set[str] = set()
        for term in [*manual_terms, *selected_terms]:
            term_key = term.lower()
            if term_key in seen:
                continue
            seen.add(term_key)
            tag_terms.append(term)

        if not tag_terms:
            raise ValueError("Enter a search term or select at least one tag.")

        tags_path = Path(DEFAULT_TAGS_FILE_PATH)
        if not tags_path.exists():
            raise FileNotFoundError(f"Tags CSV not found: {tags_path}")

        scores_path = Path(DEFAULT_SCORES_EXCEL_PATH)
        if not scores_path.exists():
            raise FileNotFoundError(f"Scores Excel not found: {scores_path}")

        _, indicators = scan_tags_for_indicators_sorted(
            tags_file_path=str(tags_path),
            tag_terms=tag_terms,
            tag_column=DEFAULT_TAG_COLUMN,
            match_mode=DEFAULT_MATCH_MODE,
            case_sensitive=DEFAULT_CASE_SENSITIVE,
            multi_input_mode=DEFAULT_MULTI_INPUT_MODE,
            chunksize=DEFAULT_CHUNKSIZE,
        )

        scores_df = pd.read_excel(scores_path)
        indicator_col = next(
            (c for c in ["indicator", "Indicator", "INDICATOR"] if c in scores_df.columns),
            None,
        )
        if indicator_col is None:
            raise KeyError(
                "Could not find an indicator column in the scores Excel. "
                f"Columns: {list(scores_df.columns)}"
            )

        scores_df["_indicator_norm"] = scores_df[indicator_col].astype("string").str.strip()
        scores_filtered = sort_scores_by_htoc_threat_desc(
            filter_scores_by_indicators_sorted(scores_df=scores_df, indicator_order=indicators)
        )

        display_df = scores_filtered.head(DEFAULT_MAX_ROWS)
        score_unique_indicators = (
            scores_filtered[indicator_col]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        indicators_df = pd.DataFrame({"indicator": score_unique_indicators}).head(
            DEFAULT_MAX_ROWS
        )
        indicators_count_text = f"Unique indicators: **{len(score_unique_indicators):,}**"

        if save_to_csv:
            out_path = _save_scores_csv(scores_filtered, output_csv_name)
            return (
                display_df,
                indicators_df,
                indicators_count_text,
                f"Saved CSV: `{out_path}`",
            )

        return display_df, indicators_df, indicators_count_text, ""
    except Exception as exc:  # Keep UI responsive with readable errors.
        return pd.DataFrame({"Error": [str(exc)]}), pd.DataFrame(), "", ""
with gr.Blocks(title="Indicator Search by Tags") as demo:
    gr.Markdown("## Search Indicators by Tags")
    gr.Markdown(
        "Enter search terms and/or choose tags to run with the default data sources."
    )
    available_tags = _load_available_tags(
        Path(DEFAULT_TAGS_FILE_PATH), tag_column=DEFAULT_TAG_COLUMN
    )
    tags_dropdown = gr.Dropdown(
        label="Select Tags",
        choices=available_tags,
        multiselect=True,
        value=[],
    )
    search_terms = gr.Textbox(
        label="Search Terms (comma or newline separated)",
        placeholder="phishing, malspam",
        lines=3,
    )
    save_to_csv = gr.Checkbox(label="Save results to CSV", value=False)
    output_csv_name = gr.Textbox(
        label="Optional CSV filename",
        placeholder="threat_scores.csv",
        lines=1,
    )

    run_btn = gr.Button("Run Search", variant="primary")
    scores_out = gr.Dataframe(
        label="Threat Assessment Scores (Matched by Indicator)",
        interactive=False,
    )
    indicators_out = gr.Dataframe(
        label="Unique Indicators",
        interactive=False,
    )
    indicators_count = gr.Markdown()
    save_status = gr.Markdown()

    run_btn.click(
        fn=run_search,
        inputs=[search_terms, tags_dropdown, save_to_csv, output_csv_name],
        outputs=[scores_out, indicators_out, indicators_count, save_status],
    )


if __name__ == "__main__":
    demo.launch(inbrowser=True)
