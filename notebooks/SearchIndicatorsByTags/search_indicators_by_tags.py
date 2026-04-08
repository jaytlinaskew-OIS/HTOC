"""
Search observed indicators by tag and pull Threat Assessment Scores by indicator.

Behavior:
- Streams `htoc_observed_indicator_tags.csv` in chunks (no full CSV load).
- Filters rows by one or more tag search terms (comma/newline separated).
- Sorts matching rows by the selected tag column, then by indicator.
- Pulls matching records from `Threat_Assessment_Scores.xlsx` using the resulting
  unique indicators list (sorted to match the tag order).
- Prints Threat Assessment Scores as a **compact table** by default (key columns only;
  use --all-score-columns for every field). Table uses tabulate "simple" layout for cmd.exe.

Typical usage:
  py search_indicators_by_tags.py --search "phishing" --tag-column tag
  py search_indicators_by_tags.py --interactive
  py -m pip install tabulate   # nicer ASCII tables (--output-format table, default)

  py search_indicators_by_tags.py --search malspam --display-columns "Indicator,Severity,PRISM Score"
  py search_indicators_by_tags.py --search malspam --output-format csv > out.csv

Dependencies (pip): wheels under Z:\\HTOC\\JA\\wheelhouse — run
run_search_indicators_by_tags.bat populate to download; double-click the same .bat to install and run.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import os
import re
import shutil
from pathlib import Path
from typing import Literal

import pandas as pd

DEFAULT_TAGS_FILE_PATH = (
    r"Z:\HTOC\Data_Analytics\Data\Observed_Tags\htoc_observed_indicator_tags.csv"
)
DEFAULT_SCORES_EXCEL_PATH = (
    r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\Threat_Assessment_Scores.xlsx"
)

AUTO_SAVED_SEARCH_FILES_DIR = Path(
    r"Z:\HTOC\Data_Analytics\Data\Threat Assessment Scores\Saved Search Files"
)

# Default console columns for Threat Assessment Scores (compact).
DEFAULT_SCORES_CONSOLE_COLUMNS: list[str] = [
    "Indicator",
    "Last Observed",
    "Indicator Type",
    "PRISM Score",
    "Severity",
    "Partners",
]

MatchMode = Literal["contains", "exact"]
MultiInputMode = Literal["any", "all"]


def _normalize_tag_series(s: pd.Series) -> pd.Series:
    return s.astype("string").str.strip()


def _parse_terms(s: str) -> list[str]:
    return [
        t.strip()
        for t in str(s).replace("\n", ",").split(",")
        if str(t).strip()
    ]


def _column_name_ci(df: pd.DataFrame, want: str) -> str | None:
    """Return actual column name matching want case-insensitively, or None."""
    key = want.strip().lower()
    for c in df.columns:
        if str(c).strip().lower() == key:
            return str(c)
    return None


def sort_scores_by_prism_desc(df: pd.DataFrame) -> pd.DataFrame:
    """Sort rows by PRISM Score descending (highest first)."""
    if df.empty:
        return df
    # Backward compatibility: support legacy score column if present.
    col = _column_name_ci(df, "PRISM Score") or _column_name_ci(
        df, "HTOC Threat Score"
    )
    if not col:
        return df
    tmp = df.copy()
    tmp["_hts"] = pd.to_numeric(tmp[col], errors="coerce")
    out = tmp.sort_values("_hts", ascending=False, na_position="last").drop(
        columns=["_hts"]
    )
    return out.reset_index(drop=True)


def _single_line_cell(value: object, max_len: int) -> str:
    """One line per cell: collapse whitespace/newlines, then truncate."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    s = re.sub(r"\s+", " ", str(value).strip())
    if max_len <= 0:
        return s
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def _dataframe_for_display(
    df: pd.DataFrame,
    *,
    max_col_width: int,
    columns: list[str] | None,
    column_width_overrides: dict[str, int] | None = None,
) -> pd.DataFrame:
    """Copy + optional column subset + single-line string truncation for tables."""
    if df.empty:
        return df
    out = df.copy()
    if columns:
        keep = [c for c in columns if c in out.columns]
        missing = [c for c in columns if c not in out.columns]
        if missing:
            print(f"Note: unknown display column(s) ignored: {missing}")
        out = out[keep]
    for col in out.columns:
        w = max_col_width
        if column_width_overrides and col in column_width_overrides:
            w = column_width_overrides[col]
        out[col] = out[col].map(lambda v, _w=w: _single_line_cell(v, _w))
    return out


def _effective_cell_width(
    *,
    num_columns: int,
    user_max: int,
    term_width: int,
    fit_terminal: bool,
) -> int:
    """Pick a per-cell width so each row is one logical line (no embedded newlines)."""
    if not fit_terminal:
        return user_max if user_max > 0 else 10_000
    n = max(1, num_columns + 1)  # +1 for row index in printed table
    # Leave room for tabulate/simple spacing; avoid tiny cells (breaks alignment on Windows).
    budget = max(48, term_width - 16 - 4 * n)
    auto = max(14, budget // n)
    if user_max <= 0:
        return auto
    return min(user_max, auto)


def _resolve_score_console_columns(df: pd.DataFrame) -> list[str]:
    """Map DEFAULT_SCORES_CONSOLE_COLUMNS to actual sheet column names (case-insensitive)."""
    if df.empty or not len(df.columns):
        return []
    by_lower = {str(c).strip().lower(): c for c in df.columns}
    out: list[str] = []
    for want in DEFAULT_SCORES_CONSOLE_COLUMNS:
        if want in df.columns:
            out.append(want)
            continue
        key = want.strip().lower()
        if key in by_lower:
            out.append(by_lower[key])
    return out if out else list(df.columns)[:6]


def print_dataframe_cli(
    df: pd.DataFrame,
    *,
    output_format: str,
    max_col_width: int,
    display_columns: list[str] | None,
    fit_terminal: bool = True,
    title: str | None = None,
    column_width_overrides: dict[str, int] | None = None,
) -> None:
    """
    Print a DataFrame in a readable table form for the console.

    Table mode: each **row** is a single line (cells are flattened to one line
    and truncated). Use --no-fit-terminal and/or --max-col-width to tune width.

    output_format:
      - table: ASCII table (uses tabulate if installed, else pandas to_string)
      - wide:  legacy wide pandas output (may wrap badly in narrow terminals)
      - csv:   CSV to stdout
    """
    if title:
        tw = shutil.get_terminal_size(fallback=(100, 24)).columns
        print(f"\n{title}")
        print("-" * min(len(title) + 4, tw))

    if df.empty:
        print("(no rows)\n")
        return

    if output_format == "csv":
        cols = display_columns
        to_write = df[list(cols)] if cols else df
        print(to_write.to_csv(index=False))
        return

    if output_format == "wide":
        with pd.option_context(
            "display.max_rows",
            None,
            "display.max_columns",
            None,
            "display.width",
            0,
            "display.max_colwidth",
            None,
        ):
            print(df)
        print()
        return

    # table (default): one line per row, no multi-line cells
    term_w = shutil.get_terminal_size(fallback=(120, 24)).columns
    if display_columns:
        ncols = len([c for c in display_columns if c in df.columns])
    else:
        ncols = len(df.columns)
    eff_width = _effective_cell_width(
        num_columns=ncols,
        user_max=max_col_width,
        term_width=term_w,
        fit_terminal=fit_terminal,
    )

    # Extra width for Indicator (full hash / URL / email) and Partners (long lists).
    overrides = dict(column_width_overrides) if column_width_overrides else {}
    show_cols = display_columns if display_columns else list(df.columns)
    for c in show_cols:
        if c not in df.columns:
            continue
        cl = str(c).strip().lower()
        # Exact "Indicator" only — not "Indicator Type".
        if cl == "indicator":
            indicator_w = min(
                max(eff_width + 88, 68),
                max(68, term_w // 2),
            )
            indicator_w = max(indicator_w, eff_width)
            overrides[c] = int(indicator_w)
        elif cl == "partners":
            partners_w = min(
                max(eff_width + 56, 52),
                max(52, (term_w * 9) // 20),
            )
            partners_w = max(partners_w, eff_width)
            overrides[c] = int(partners_w)

    disp = _dataframe_for_display(
        df,
        max_col_width=eff_width,
        columns=display_columns,
        column_width_overrides=overrides if overrides else None,
    )

    try:
        from tabulate import tabulate  # type: ignore[import-untyped]

        # "simple" aligns reliably in narrow cmd windows; "grid" often breaks with many columns.
        print(
            tabulate(
                disp,
                headers="keys",
                tablefmt="simple",
                showindex=True,
                numalign="right",
                stralign="left",
            )
        )
    except ImportError:
        # No tabulate: single-line rows only (no text wrapping)
        with pd.option_context(
            "display.max_rows",
            None,
            "display.max_columns",
            None,
            "display.width",
            max(term_w, 120),
            "display.max_colwidth",
            eff_width,
            "display.expand_frame_repr",
            False,
        ):
            print(disp.to_string())
        print(
            "\nTip: install tabulate for cleaner tables: py -m pip install tabulate\n"
        )
    print()


def filter_chunk_by_tag(
    df: pd.DataFrame,
    tag_terms: list[str],
    *,
    tag_column: str,
    match_mode: MatchMode,
    case_sensitive: bool,
    multi_input_mode: MultiInputMode,
) -> pd.DataFrame:
    if tag_column not in df.columns:
        raise KeyError(
            f"tag_column '{tag_column}' not found. Available columns: {list(df.columns)}"
        )
    if not tag_terms:
        raise ValueError("No tag search terms provided")

    tags = _normalize_tag_series(df[tag_column])

    def _mask_for_term(term: str) -> pd.Series:
        if match_mode == "exact":
            if case_sensitive:
                return tags == term
            return tags.str.lower() == term.lower()
        # match_mode == "contains"
        return tags.str.contains(term, case=case_sensitive, na=False, regex=False)

    mask = None
    for term in tag_terms:
        term_mask = _mask_for_term(term)
        if mask is None:
            mask = term_mask
        elif multi_input_mode == "any":
            mask = mask | term_mask
        else:  # multi_input_mode == "all"
            mask = mask & term_mask

    return df.loc[mask].copy()


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
    # Grab columns once (cheap; reads no rows).
    columns = pd.read_csv(tags_file_path, dtype=str, nrows=0).columns

    match_chunks: list[pd.DataFrame] = []

    for chunk_idx, chunk in enumerate(
        pd.read_csv(tags_file_path, dtype=str, chunksize=chunksize),
        start=1,
    ):
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

        # Light progress for long runs.
        if chunk_idx % 20 == 0:
            print(f"Processed {chunk_idx} chunks...")

    filtered = (
        pd.concat(match_chunks, ignore_index=True)
        if match_chunks
        else pd.DataFrame(columns=columns)
    )

    # Sort by tag column, then indicator.
    if not filtered.empty and tag_column in filtered.columns:
        filtered = filtered.copy()
        filtered["_sort_tag"] = filtered[tag_column].astype("string").str.strip()

        sort_cols = ["_sort_tag"]
        if "indicator" in filtered.columns:
            filtered["_sort_indicator"] = (
                filtered["indicator"].astype("string").str.strip()
            )
            sort_cols.append("_sort_indicator")

        filtered = (
            filtered.sort_values(
                by=sort_cols,
                kind="mergesort",
                na_position="last",
            )
            .drop(
                columns=[
                    c
                    for c in ["_sort_tag", "_sort_indicator"]
                    if c in filtered.columns
                ],
                errors="ignore",
            )
            .reset_index(drop=True)
        )

    indicators: list[str] = []
    if "indicator" in filtered.columns and not filtered.empty:
        _ind_series = filtered["indicator"].astype("string").str.strip()
        _ind_series = _ind_series.loc[
            _ind_series.notna() & (_ind_series != "")
        ]
        indicators = _ind_series.drop_duplicates().tolist()

    return filtered, indicators


def load_scores_excel(
    scores_excel_path: str,
) -> tuple[pd.DataFrame, str]:
    scores_df = pd.read_excel(scores_excel_path)

    indicator_col = next(
        (c for c in ["indicator", "Indicator", "INDICATOR"] if c in scores_df.columns),
        None,
    )
    if indicator_col is None:
        raise KeyError(
            "Could not find an indicator column in the scores Excel. "
            f"Columns: {list(scores_df.columns)}"
        )

    scores_df["_indicator_norm"] = (
        scores_df[indicator_col].astype("string").str.strip()
    )
    return scores_df, indicator_col


def filter_scores_by_indicators_sorted(
    scores_df: pd.DataFrame,
    indicator_order: list[str],
) -> pd.DataFrame:
    indicator_set = set(indicator_order)
    filtered = scores_df[scores_df["_indicator_norm"].isin(indicator_set)].copy()

    # Preserve the tag-sorted indicator order without merge dtype issues.
    order_map = {ind: i for i, ind in enumerate(indicator_order)}
    filtered["_order"] = filtered["_indicator_norm"].map(order_map)

    filtered = (
        filtered.sort_values(
            "_order",
            kind="mergesort",
            na_position="last",
        )
        .drop(columns=["_indicator_norm", "_order"])
        .reset_index(drop=True)
    )
    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Filter indicators by observed tags and pull score records by indicator."
    )
    parser.add_argument(
        "--tags-file-path",
        default=DEFAULT_TAGS_FILE_PATH,
        help="Path to htoc_observed_indicator_tags.csv",
    )
    parser.add_argument(
        "--search",
        default=None,
        help="Tag criteria (comma/newline separated). Example: phishing,Malspam",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Prompt repeatedly for tag criteria until you press Enter on an empty input.",
    )
    parser.add_argument(
        "--tag-column",
        default="tag",
        help="Which column to search in htoc_observed_indicator_tags.csv: tag | orig_tag",
    )
    parser.add_argument(
        "--match",
        default="contains",
        choices=["contains", "exact"],
        help="contains=literal substring match; exact=full value match. Default: contains",
    )
    parser.add_argument(
        "--multi-input-mode",
        default="any",
        choices=["any", "all"],
        help="any=OR across terms; all=AND across terms. Default: any",
    )
    parser.add_argument(
        "--case-sensitive",
        action="store_true",
        help="Make matching case-sensitive.",
    )
    parser.add_argument(
        "--chunksize",
        type=int,
        default=5000,
        help="CSV chunksize for streaming scan. Default: 5000",
    )
    parser.add_argument(
        "--threat-scores-excel-path",
        default=DEFAULT_SCORES_EXCEL_PATH,
        help="Path to Threat_Assessment_Scores.xlsx",
    )
    parser.add_argument(
        "--clear-output",
        action="store_true",
        help="Clear console between interactive searches (Windows: cls).",
    )
    parser.add_argument(
        "--show-scores-records",
        action="store_true",
        help="Print the full matching score records to the console.",
        default=True,
    )
    parser.add_argument(
        "--no-show-scores-records",
        action="store_false",
        dest="show_scores_records",
        help="Do not print score records.",
    )
    parser.add_argument(
        "--show-tag-matching-rows",
        action="store_true",
        default=False,
        help="Also print matching rows from htoc_observed_indicator_tags.csv.",
    )
    parser.add_argument(
        "--show-indicators-list",
        action="store_true",
        default=False,
        help="Also print the unique indicator list.",
    )
    parser.add_argument(
        "--output-scores-filtered-csv",
        default=None,
        help="Optional: write the filtered score records to CSV.",
    )
    parser.add_argument(
        "--output-matching-rows-csv",
        default=None,
        help="Optional: write the matching tag rows to CSV.",
    )
    parser.add_argument(
        "--output-indicators-csv",
        default=None,
        help="Optional: write the unique indicator list to CSV.",
    )
    parser.add_argument(
        "--output-format",
        default="table",
        choices=["table", "wide", "csv"],
        help="Console layout for DataFrames: table (ASCII grid; pip install tabulate "
        "for best results), wide (raw pandas), or csv (print CSV to stdout). Default: table",
    )
    parser.add_argument(
        "--max-col-width",
        type=int,
        default=48,
        help="Max characters per cell in table mode (long values truncated). Default: 48",
    )
    parser.add_argument(
        "--display-columns",
        default=None,
        help="Comma-separated columns for console (overrides default score subset). "
        "Also used for --show-tag-matching-rows when set.",
    )
    parser.add_argument(
        "--all-score-columns",
        action="store_true",
        help="Print all Threat Assessment Scores columns (default is a compact key-column set).",
    )
    parser.set_defaults(fit_terminal=True)
    parser.add_argument(
        "--no-fit-terminal",
        action="store_false",
        dest="fit_terminal",
        help="Do not shrink column width to terminal size (still one line per row; "
        "may be wider than the window).",
    )

    args = parser.parse_args()

    tags_file_path = Path(args.tags_file_path)
    if not tags_file_path.exists():
        raise FileNotFoundError(f"CSV not found: {tags_file_path}")

    scores_excel_path = Path(args.threat_scores_excel_path)
    if not scores_excel_path.exists():
        raise FileNotFoundError(f"Scores Excel not found: {scores_excel_path}")

    match_mode: MatchMode = args.match
    multi_input_mode: MultiInputMode = args.multi_input_mode

    display_cols: list[str] | None = None
    if args.display_columns:
        display_cols = [
            c.strip() for c in args.display_columns.split(",") if c.strip()
        ]

    if args.interactive:
        print("Loading...", flush=True)

    # Load scores once.
    scores_df, indicator_col = load_scores_excel(str(scores_excel_path))

    def run_once(tag_search: str) -> None:
        tag_terms = _parse_terms(tag_search)
        if not tag_terms:
            raise ValueError("No tag criteria provided.")

        if args.clear_output and os.name == "nt":
            os.system("cls")

        safe_base = re.sub(
            r"[^A-Za-z0-9_-]+",
            "_",
            "_".join(tag_terms)[:80],
        ).strip("_")
        if not safe_base:
            safe_base = "results"

        print(f"Searching for terms: {tag_terms}")
        print(
            f"(tag_column={args.tag_column}, match_mode={match_mode}, multi_input_mode={multi_input_mode})"
        )

        filtered_tags, indicators = scan_tags_for_indicators_sorted(
            tags_file_path=str(tags_file_path),
            tag_terms=tag_terms,
            tag_column=args.tag_column,
            match_mode=match_mode,
            case_sensitive=args.case_sensitive,
            multi_input_mode=multi_input_mode,
            chunksize=args.chunksize,
        )

        print(
            f"Matched tag rows: {len(filtered_tags)}; unique indicators: {len(indicators)}"
        )

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

        scores_filtered = sort_scores_by_prism_desc(
            filter_scores_by_indicators_sorted(
                scores_df=scores_df,
                indicator_order=indicators,
            )
        )

        print(
            f"Scores rows matched: {len(scores_filtered)} (indicator_column={indicator_col})."
        )

        if args.show_scores_records:
            if args.all_score_columns:
                score_console_cols: list[str] | None = None
            elif display_cols:
                score_console_cols = display_cols
            else:
                score_console_cols = _resolve_score_console_columns(scores_filtered)

            print_dataframe_cli(
                scores_filtered,
                output_format=args.output_format,
                max_col_width=args.max_col_width,
                display_columns=score_console_cols,
                fit_terminal=args.fit_terminal,
                title="Threat Assessment Scores (matched by indicator)",
            )
        if args.output_scores_filtered_csv:
            out_path = Path(args.output_scores_filtered_csv)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            scores_filtered.to_csv(out_path, index=False)
            print(f"Wrote scores filtered CSV: {out_path}")

        if args.output_matching_rows_csv:
            out_path = Path(args.output_matching_rows_csv)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            filtered_tags.to_csv(out_path, index=False)
            print(f"Wrote matching tag rows CSV: {out_path}")

        if args.output_indicators_csv:
            out_path = Path(args.output_indicators_csv)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            pd.DataFrame({"indicator": indicators}).to_csv(out_path, index=False)
            print(f"Wrote unique indicators CSV: {out_path}")

        # Interactive-only: let the user opt in to saving threat scores CSV
        # into the shared folder requested by the user.
        if args.interactive:
            resp = input(
                "Save threat scores CSV into Saved Search Files folder? [y/N]: "
            ).strip().lower()
            if resp in ("y", "yes"):
                AUTO_SAVED_SEARCH_FILES_DIR.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                out_path = (
                    AUTO_SAVED_SEARCH_FILES_DIR
                    / f"{safe_base}_threat_scores_{stamp}.csv"
                )
                scores_filtered.to_csv(out_path, index=False)
                print(f"Wrote threat scores CSV: {out_path}")

    if args.interactive:
        while True:
            tag_search = input(
                "Enter tag criteria (comma-separated). Press Enter on blank to end: "
            ).strip()
            if not tag_search:
                break
            run_once(tag_search)
    else:
        if not args.search:
            raise ValueError("Provide --search or use --interactive.")
        run_once(args.search)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

