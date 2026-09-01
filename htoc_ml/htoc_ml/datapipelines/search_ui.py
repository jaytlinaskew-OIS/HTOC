"""Optional Gradio front end for tag search. Requires: pip install gradio."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from htoc_ml.datapipelines.search_tags import (
    default_saved_search_dir,
    default_scores_path,
    default_tags_path,
    filter_scores_by_indicators_sorted,
    load_scores_excel,
    parse_terms,
    scan_tags_for_indicators_sorted,
    sort_scores_by_prism_desc,
)

DEFAULT_TAG_COLUMN = "tag"
DEFAULT_CHUNKSIZE = 5000
DEFAULT_MAX_ROWS = 500


def load_available_tags(tags_file_path: Path, tag_column: str) -> list[str]:
    if not tags_file_path.exists():
        return []
    unique_tags: set[str] = set()
    try:
        for chunk in pd.read_csv(
            tags_file_path, dtype=str, usecols=[tag_column], chunksize=DEFAULT_CHUNKSIZE
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


def save_scores_csv(scores_df: pd.DataFrame, requested_name: str) -> Path:
    target_dir = default_saved_search_dir()
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
        manual_terms = parse_terms(search_terms)
        selected_terms = [str(t).strip() for t in (selected_tags or []) if str(t).strip()]
        tag_terms: list[str] = []
        seen: set[str] = set()
        for term in [*manual_terms, *selected_terms]:
            key = term.lower()
            if key in seen:
                continue
            seen.add(key)
            tag_terms.append(term)
        if not tag_terms:
            raise ValueError("Enter a search term or select at least one tag.")
        tags_path = default_tags_path()
        if not tags_path.exists():
            raise FileNotFoundError(f"Tags CSV not found: {tags_path}")
        scores_path = default_scores_path()
        if not scores_path.exists():
            raise FileNotFoundError(f"Scores Excel not found: {scores_path}")
        _, indicators = scan_tags_for_indicators_sorted(
            tags_file_path=str(tags_path),
            tag_terms=tag_terms,
            tag_column=DEFAULT_TAG_COLUMN,
            match_mode="contains",
            case_sensitive=False,
            multi_input_mode="any",
            chunksize=DEFAULT_CHUNKSIZE,
        )
        scores_df, indicator_col = load_scores_excel(str(scores_path))
        scores_filtered = sort_scores_by_prism_desc(
            filter_scores_by_indicators_sorted(scores_df, indicators)
        )
        display_df = scores_filtered.head(DEFAULT_MAX_ROWS)
        score_unique = (
            scores_filtered[indicator_col]
            .astype("string")
            .str.strip()
            .replace("", pd.NA)
            .dropna()
            .drop_duplicates()
            .tolist()
        )
        indicators_df = pd.DataFrame({"indicator": score_unique}).head(DEFAULT_MAX_ROWS)
        count_text = f"Unique indicators: **{len(score_unique):,}**"
        if save_to_csv:
            out_path = save_scores_csv(scores_filtered, output_csv_name)
            return display_df, indicators_df, count_text, f"Saved CSV: `{out_path}`"
        return display_df, indicators_df, count_text, ""
    except Exception as exc:
        return pd.DataFrame({"Error": [str(exc)]}), pd.DataFrame(), "", ""


def launch() -> None:
    try:
        import gradio as gr
    except ImportError as exc:
        raise SystemExit("Gradio is not installed. py -m pip install gradio") from exc

    tags_path = default_tags_path()
    available_tags = load_available_tags(tags_path, DEFAULT_TAG_COLUMN)
    with gr.Blocks(title="Indicator Search by Tags") as demo:
        gr.Markdown("## Search Indicators by Tags")
        gr.Markdown("Enter search terms and/or choose tags. Uses the live tags CSV and PRISM workbook.")
        tags_dropdown = gr.Dropdown(
            label="Select Tags", choices=available_tags, multiselect=True, value=[]
        )
        search_box = gr.Textbox(
            label="Search Terms (comma or newline separated)",
            placeholder="phishing, malspam",
            lines=3,
        )
        save_to_csv = gr.Checkbox(label="Save results to CSV", value=False)
        output_csv_name = gr.Textbox(label="Optional CSV filename", placeholder="threat_scores.csv")
        run_btn = gr.Button("Run Search", variant="primary")
        scores_out = gr.Dataframe(label="Threat Assessment Scores (Matched by Indicator)", interactive=False)
        indicators_out = gr.Dataframe(label="Unique Indicators", interactive=False)
        indicators_count = gr.Markdown()
        save_status = gr.Markdown()
        run_btn.click(
            fn=run_search,
            inputs=[search_box, tags_dropdown, save_to_csv, output_csv_name],
            outputs=[scores_out, indicators_out, indicators_count, save_status],
        )
    demo.launch(inbrowser=True)
