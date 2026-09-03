"""Filter observed-indicator tags and pull matching PRISM score rows."""
from __future__ import annotations

import argparse
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from htoc.datapipelines.paths import env_path, share_root

MatchMode = Literal["contains", "exact"]
MultiInputMode = Literal["any", "all"]

DEFAULT_SCORES_CONSOLE_COLUMNS = [
    "Indicator",
    "Last Observed",
    "Indicator Type",
    "PRISM Score",
    "Severity",
    "Partners",
]


def default_tags_path() -> Path:
    return env_path(
        "HTOC_TAGS_CSV",
        share_root() / "Data_Analytics" / "Data" / "Observed_Tags" / "htoc_observed_indicator_tags.csv",
    )


def default_scores_path() -> Path:
    return env_path(
        "HTOC_SCORES_XLSX",
        share_root() / "Data_Analytics" / "Data" / "Threat Assessment Scores" / "Threat_Assessment_Scores.xlsx",
    )


def default_saved_search_dir() -> Path:
    return env_path(
        "HTOC_SAVED_SEARCH_DIR",
        share_root() / "Data_Analytics" / "Data" / "Threat Assessment Scores" / "Saved Search Files",
    )


def parse_terms(raw: str) -> list[str]:
    return [part.strip() for part in str(raw).replace("\n", ",").split(",") if str(part).strip()]


def column_name_ci(frame: pd.DataFrame, want: str) -> str | None:
    key = want.strip().lower()
    for col in frame.columns:
        if str(col).strip().lower() == key:
            return str(col)
    return None


def sort_scores_by_prism_desc(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    col = column_name_ci(frame, "PRISM Score") or column_name_ci(frame, "HTOC Threat Score")
    if not col:
        return frame
    tmp = frame.copy()
    tmp["_hts"] = pd.to_numeric(tmp[col], errors="coerce")
    return (
        tmp.sort_values("_hts", ascending=False, na_position="last")
        .drop(columns=["_hts"])
        .reset_index(drop=True)
    )


def filter_chunk_by_tag(
    frame: pd.DataFrame,
    tag_terms: list[str],
    *,
    tag_column: str,
    match_mode: MatchMode,
    case_sensitive: bool,
    multi_input_mode: MultiInputMode,
) -> pd.DataFrame:
    if tag_column not in frame.columns:
        raise KeyError(f"tag_column {tag_column!r} not found. Available: {list(frame.columns)}")
    if not tag_terms:
        raise ValueError("No tag search terms provided")
    tags = frame[tag_column].astype("string").str.strip()

    def mask_for_term(term: str) -> pd.Series:
        if match_mode == "exact":
            return tags == term if case_sensitive else tags.str.lower() == term.lower()
        return tags.str.contains(term, case=case_sensitive, na=False, regex=False)

    mask = None
    for term in tag_terms:
        term_mask = mask_for_term(term)
        mask = term_mask if mask is None else (mask | term_mask if multi_input_mode == "any" else mask & term_mask)
    return frame.loc[mask].copy()


def scan_tags_for_indicators_sorted(
    *,
    tags_file_path: str,
    tag_terms: list[str],
    tag_column: str,
    match_mode: MatchMode,
    case_sensitive: bool,
    multi_input_mode: MultiInputMode,
    chunksize: int,
) -> tuple[pd.DataFrame, list[str]]:
    columns = pd.read_csv(tags_file_path, dtype=str, nrows=0).columns
    match_chunks: list[pd.DataFrame] = []
    for chunk_idx, chunk in enumerate(pd.read_csv(tags_file_path, dtype=str, chunksize=chunksize), start=1):
        filtered_chunk = filter_chunk_by_tag(
            chunk,
            tag_terms,
            tag_column=tag_column,
            match_mode=match_mode,
            case_sensitive=case_sensitive,
            multi_input_mode=multi_input_mode,
        )
        if not filtered_chunk.empty:
            match_chunks.append(filtered_chunk)
        if chunk_idx % 20 == 0:
            print(f"Processed {chunk_idx} chunks...")
    filtered = pd.concat(match_chunks, ignore_index=True) if match_chunks else pd.DataFrame(columns=columns)
    if not filtered.empty and tag_column in filtered.columns:
        filtered = filtered.copy()
        filtered["_sort_tag"] = filtered[tag_column].astype("string").str.strip()
        sort_cols = ["_sort_tag"]
        if "indicator" in filtered.columns:
            filtered["_sort_indicator"] = filtered["indicator"].astype("string").str.strip()
            sort_cols.append("_sort_indicator")
        filtered = (
            filtered.sort_values(by=sort_cols, kind="mergesort", na_position="last")
            .drop(columns=[c for c in ["_sort_tag", "_sort_indicator"] if c in filtered.columns], errors="ignore")
            .reset_index(drop=True)
        )
    indicators: list[str] = []
    if "indicator" in filtered.columns and not filtered.empty:
        series = filtered["indicator"].astype("string").str.strip()
        series = series.loc[series.notna() & (series != "")]
        indicators = series.drop_duplicates().tolist()
    return filtered, indicators


def load_scores_excel(scores_excel_path: str) -> tuple[pd.DataFrame, str]:
    scores = pd.read_excel(scores_excel_path)
    indicator_col = next((c for c in ["indicator", "Indicator", "INDICATOR"] if c in scores.columns), None)
    if indicator_col is None:
        raise KeyError(f"No indicator column in scores Excel. Columns: {list(scores.columns)}")
    scores["_indicator_norm"] = scores[indicator_col].astype("string").str.strip()
    return scores, indicator_col


def filter_scores_by_indicators_sorted(scores_df: pd.DataFrame, indicator_order: list[str]) -> pd.DataFrame:
    filtered = scores_df[scores_df["_indicator_norm"].isin(set(indicator_order))].copy()
    order_map = {ind: i for i, ind in enumerate(indicator_order)}
    filtered["_order"] = filtered["_indicator_norm"].map(order_map)
    return (
        filtered.sort_values("_order", kind="mergesort", na_position="last")
        .drop(columns=["_indicator_norm", "_order"])
        .reset_index(drop=True)
    )


def _single_line_cell(value: object, max_len: int) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = re.sub(r"\s+", " ", str(value).strip())
    if max_len <= 0 or len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def _dataframe_for_display(
    frame: pd.DataFrame,
    *,
    max_col_width: int,
    columns: list[str] | None,
    column_width_overrides: dict[str, int] | None = None,
) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    if columns:
        keep = [c for c in columns if c in out.columns]
        missing = [c for c in columns if c not in out.columns]
        if missing:
            print(f"Note: unknown display column(s) ignored: {missing}")
        out = out[keep]
    for col in out.columns:
        width = (column_width_overrides or {}).get(col, max_col_width)
        out[col] = out[col].map(lambda v, _w=width: _single_line_cell(v, _w))
    return out


def resolve_score_console_columns(frame: pd.DataFrame) -> list[str]:
    if frame.empty or not len(frame.columns):
        return []
    by_lower = {str(c).strip().lower(): c for c in frame.columns}
    out: list[str] = []
    for want in DEFAULT_SCORES_CONSOLE_COLUMNS:
        if want in frame.columns:
            out.append(want)
        elif want.strip().lower() in by_lower:
            out.append(by_lower[want.strip().lower()])
    return out if out else list(frame.columns)[:6]


def print_dataframe_cli(
    frame: pd.DataFrame,
    *,
    output_format: str,
    max_col_width: int,
    display_columns: list[str] | None,
    fit_terminal: bool = True,
    title: str | None = None,
    column_width_overrides: dict[str, int] | None = None,
) -> None:
    if title:
        term_w = shutil.get_terminal_size(fallback=(100, 24)).columns
        print(f"\n{title}")
        print("-" * min(len(title) + 4, term_w))
    if frame.empty:
        print("(no rows)\n")
        return
    if output_format == "csv":
        to_write = frame[list(display_columns)] if display_columns else frame
        print(to_write.to_csv(index=False))
        return
    if output_format == "wide":
        with pd.option_context("display.max_rows", None, "display.max_columns", None, "display.width", 0, "display.max_colwidth", None):
            print(frame)
        print()
        return
    term_w = shutil.get_terminal_size(fallback=(120, 24)).columns
    ncols = len([c for c in display_columns if c in frame.columns]) if display_columns else len(frame.columns)
    if not fit_terminal:
        eff_width = max_col_width if max_col_width > 0 else 10_000
    else:
        n = max(1, ncols + 1)
        budget = max(48, term_w - 16 - 4 * n)
        auto = max(14, budget // n)
        eff_width = auto if max_col_width <= 0 else min(max_col_width, auto)
    overrides = dict(column_width_overrides) if column_width_overrides else {}
    show_cols = display_columns if display_columns else list(frame.columns)
    for col in show_cols:
        if col not in frame.columns:
            continue
        cl = str(col).strip().lower()
        if cl == "indicator":
            overrides[col] = int(max(min(max(eff_width + 88, 68), max(68, term_w // 2)), eff_width))
        elif cl == "partners":
            overrides[col] = int(max(min(max(eff_width + 56, 52), max(52, (term_w * 9) // 20)), eff_width))
    disp = _dataframe_for_display(
        frame, max_col_width=eff_width, columns=display_columns, column_width_overrides=overrides or None
    )
    try:
        from tabulate import tabulate

        print(tabulate(disp, headers="keys", tablefmt="simple", showindex=True, numalign="right", stralign="left"))
    except ImportError:
        with pd.option_context(
            "display.max_rows", None, "display.max_columns", None,
            "display.width", max(term_w, 120), "display.max_colwidth", eff_width,
            "display.expand_frame_repr", False,
        ):
            print(disp.to_string())
        print("\nTip: install tabulate for cleaner tables: py -m pip install tabulate\n")
    print()


def search_once(
    *,
    tag_search: str,
    tags_file_path: Path,
    scores_df: pd.DataFrame,
    indicator_col: str,
    tag_column: str,
    match_mode: MatchMode,
    multi_input_mode: MultiInputMode,
    case_sensitive: bool,
    chunksize: int,
) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    tag_terms = parse_terms(tag_search)
    if not tag_terms:
        raise ValueError("No tag criteria provided.")
    filtered_tags, indicators = scan_tags_for_indicators_sorted(
        tags_file_path=str(tags_file_path),
        tag_terms=tag_terms,
        tag_column=tag_column,
        match_mode=match_mode,
        case_sensitive=case_sensitive,
        multi_input_mode=multi_input_mode,
        chunksize=chunksize,
    )
    scores_filtered = sort_scores_by_prism_desc(
        filter_scores_by_indicators_sorted(scores_df, indicators)
    )
    return filtered_tags, indicators, scores_filtered


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Filter indicators by observed tags and pull PRISM score records."
    )
    parser.add_argument("--tags-file-path", default=str(default_tags_path()))
    parser.add_argument("--search", default=None, help="Tag criteria, comma/newline separated.")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--ui", action="store_true", help="Launch the Gradio UI (requires gradio).")
    parser.add_argument("--tag-column", default="tag")
    parser.add_argument("--match", default="contains", choices=["contains", "exact"])
    parser.add_argument("--multi-input-mode", default="any", choices=["any", "all"])
    parser.add_argument("--case-sensitive", action="store_true")
    parser.add_argument("--chunksize", type=int, default=5000)
    parser.add_argument("--threat-scores-excel-path", default=str(default_scores_path()))
    parser.add_argument("--clear-output", action="store_true")
    parser.add_argument("--show-scores-records", action="store_true", default=True)
    parser.add_argument("--no-show-scores-records", action="store_false", dest="show_scores_records")
    parser.add_argument("--show-tag-matching-rows", action="store_true")
    parser.add_argument("--show-indicators-list", action="store_true")
    parser.add_argument("--output-scores-filtered-csv", default=None)
    parser.add_argument("--output-matching-rows-csv", default=None)
    parser.add_argument("--output-indicators-csv", default=None)
    parser.add_argument("--output-format", default="table", choices=["table", "wide", "csv"])
    parser.add_argument("--max-col-width", type=int, default=48)
    parser.add_argument("--display-columns", default=None)
    parser.add_argument("--all-score-columns", action="store_true")
    parser.set_defaults(fit_terminal=True)
    parser.add_argument("--no-fit-terminal", action="store_false", dest="fit_terminal")
    args = parser.parse_args(argv)

    if args.ui:
        from htoc.datapipelines.search_ui import launch

        launch()
        return 0

    tags_file_path = Path(args.tags_file_path)
    if not tags_file_path.exists():
        raise FileNotFoundError(f"CSV not found: {tags_file_path}")
    scores_excel_path = Path(args.threat_scores_excel_path)
    if not scores_excel_path.exists():
        raise FileNotFoundError(f"Scores Excel not found: {scores_excel_path}")

    display_cols = [c.strip() for c in args.display_columns.split(",") if c.strip()] if args.display_columns else None
    if args.interactive:
        print("Loading...", flush=True)
    scores_df, indicator_col = load_scores_excel(str(scores_excel_path))

    def run_once(tag_search: str) -> None:
        if args.clear_output and os.name == "nt":
            os.system("cls")
        tag_terms = parse_terms(tag_search)
        print(f"Searching for terms: {tag_terms}")
        filtered_tags, indicators, scores_filtered = search_once(
            tag_search=tag_search,
            tags_file_path=tags_file_path,
            scores_df=scores_df,
            indicator_col=indicator_col,
            tag_column=args.tag_column,
            match_mode=args.match,
            multi_input_mode=args.multi_input_mode,
            case_sensitive=args.case_sensitive,
            chunksize=args.chunksize,
        )
        print(f"Matched tag rows: {len(filtered_tags)}; unique indicators: {len(indicators)}")
        if args.show_indicators_list:
            print_dataframe_cli(
                pd.DataFrame({"indicator": indicators}),
                output_format=args.output_format,
                max_col_width=args.max_col_width,
                display_columns=None,
                fit_terminal=args.fit_terminal,
                title="Matching indicators",
            )
        if args.show_tag_matching_rows:
            print_dataframe_cli(
                filtered_tags,
                output_format=args.output_format,
                max_col_width=args.max_col_width,
                display_columns=display_cols,
                fit_terminal=args.fit_terminal,
                title="Observed tag rows (matched)",
            )
        print(f"Scores rows matched: {len(scores_filtered)} (indicator_column={indicator_col}).")
        if args.show_scores_records:
            if args.all_score_columns:
                score_cols = None
            elif display_cols:
                score_cols = display_cols
            else:
                score_cols = resolve_score_console_columns(scores_filtered)
            print_dataframe_cli(
                scores_filtered,
                output_format=args.output_format,
                max_col_width=args.max_col_width,
                display_columns=score_cols,
                fit_terminal=args.fit_terminal,
                title="Threat Assessment Scores (matched by indicator)",
            )
        for path, frame in (
            (args.output_scores_filtered_csv, scores_filtered),
            (args.output_matching_rows_csv, filtered_tags),
            (args.output_indicators_csv, pd.DataFrame({"indicator": indicators})),
        ):
            if path:
                out = Path(path)
                out.parent.mkdir(parents=True, exist_ok=True)
                frame.to_csv(out, index=False)
                print(f"Wrote {out}")
        if args.interactive:
            resp = input("Save threat scores CSV into Saved Search Files folder? [y/N]: ").strip().lower()
            if resp in ("y", "yes"):
                saved = default_saved_search_dir()
                saved.mkdir(parents=True, exist_ok=True)
                safe_base = re.sub(r"[^A-Za-z0-9_-]+", "_", "_".join(tag_terms)[:80]).strip("_") or "results"
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out = saved / f"{safe_base}_threat_scores_{stamp}.csv"
                scores_filtered.to_csv(out, index=False)
                print(f"Wrote threat scores CSV: {out}")

    if args.interactive:
        while True:
            tag_search = input("Enter tag criteria (comma-separated). Press Enter on blank to end: ").strip()
            if not tag_search:
                break
            run_once(tag_search)
    else:
        if not args.search:
            raise ValueError("Provide --search, --interactive, or --ui.")
        run_once(args.search)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
