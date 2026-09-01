import pandas as pd

from htoc_ml.datapipelines.iw_listing import (
    combine_pdf_extractions,
    description_from_title,
    fill_master_sheet,
    is_defanged_ip,
    serial_from_pdf_name,
)
from htoc_ml.datapipelines.search_tags import filter_chunk_by_tag, parse_terms
from htoc_ml.datapipelines.triage import classify_indicator, run_triage


def test_parse_terms_splits_comma_and_newline():
    assert parse_terms("phishing, malspam\ntor") == ["phishing", "malspam", "tor"]


def test_tag_filter_any_and_all():
    frame = pd.DataFrame(
        {
            "tag": ["malspam", "phishing kit", "tor node"],
            "indicator": ["a", "b", "c"],
        }
    )
    any_hit = filter_chunk_by_tag(
        frame, ["phish", "tor"], tag_column="tag", match_mode="contains",
        case_sensitive=False, multi_input_mode="any",
    )
    assert set(any_hit["indicator"]) == {"b", "c"}
    all_hit = filter_chunk_by_tag(
        frame, ["phish", "kit"], tag_column="tag", match_mode="contains",
        case_sensitive=False, multi_input_mode="all",
    )
    assert list(all_hit["indicator"]) == ["b"]
    exact = filter_chunk_by_tag(
        frame, ["malspam"], tag_column="tag", match_mode="exact",
        case_sensitive=False, multi_input_mode="any",
    )
    assert list(exact["indicator"]) == ["a"]


def test_classify_bulletproof_and_cloud():
    bad = classify_indicator(
        {"isp": "FlokiNET", "org": "unmanaged", "proxy": False, "hosting": True, "country": "Iceland", "as": "AS123"},
        {},
        "Address",
    )
    assert bad["behavior"] == "malicious_infrastructure"
    assert bad["score_recommendation"] == "elevate_score"
    cloud = classify_indicator(
        {"isp": "Amazon.com", "org": "AWS", "proxy": False, "hosting": True, "country": "United States", "as": "AS16509"},
        {},
        "Address",
    )
    assert cloud["behavior"] == "cloud_hosted"
    assert cloud["score_recommendation"] == "reduce_score"
    host = classify_indicator({}, {}, "Host")
    assert host["behavior"] == "non_ip"


def test_triage_writes_csv_without_network(tmp_path):
    scores = pd.DataFrame(
        {
            "Indicator": ["1.2.3.4", "evil.example"],
            "Indicator Type": ["Address", "Host"],
        }
    )
    xlsx = tmp_path / "scores.xlsx"
    scores.to_excel(xlsx, sheet_name="PRISM Scores", index=False)

    def fake_lookup(ips):
        return {ip: {"isp": "Amazon.com", "org": "AWS", "hosting": True, "proxy": False, "country": "US", "as": "AS16509", "countryCode": "US"} for ip in ips}

    out = tmp_path / "triage.csv"
    ckpt = tmp_path / "ckpt.txt"
    run_triage(
        scores_path=xlsx,
        output_path=out,
        checkpoint_path=ckpt,
        lookup_fn=fake_lookup,
        pause_s=0.0,
    )
    result = pd.read_csv(out)
    assert set(result["Indicator"].astype(str)) == {"1.2.3.4", "evil.example"}
    assert "cloud_hosted" in set(result["behavior"])
    assert "non_ip" in set(result["behavior"])


def test_iw_listing_combines_pdf_tables():
    title = "HTOC—Four Possibly Malicious Dutch TOR Nodes Seen in Observations"
    assert "Four Possibly Malicious Dutch TOR Nodes" in description_from_title(title)
    assert serial_from_pdf_name("HTOC-20250624-1015-A.pdf") == "20250624-1015-A"
    tables = pd.DataFrame(
        {
            "Indicators/Identifiers": ["45.90.185[.]101", "45.90.185[.]119"],
            "Indicator Type": ["IPv4 Address", "IPv4 Address"],
            "Observed By": ["FDA\nVA", "NIH"],
        }
    )
    combined = combine_pdf_extractions(
        {
            "HTOC-20250624-1015-A.pdf": {
                "title_serial_paragraph": title,
                "tables": [{"dataframe": tables}],
            }
        }
    )
    assert len(combined) == 2
    assert combined.iloc[0]["I&W Serial"] == "20250624-1015-A"
    assert "TOR Nodes" in combined.iloc[0]["Description"]


def test_defanged_ip_and_master_sheet(tmp_path):
    assert is_defanged_ip("45.90.185[.]101")
    assert not is_defanged_ip("not an address")
    out = tmp_path / "Master.xlsx"
    fill_master_sheet(
        out,
        "Master Sheet",
        [{"HTOC_Like_Data": "HTOC-20250624-1015-A", "IP_Like_Data": "1.2.3[.]4", "Keyword": "FDA"}],
        "06/24/2025",
    )
    frame = pd.read_excel(out, sheet_name="Master Sheet")
    assert frame.iloc[0]["Partner"] == "FDA"
    assert frame.iloc[0]["Bi-Weekly Date"] == "06/24/2025"
