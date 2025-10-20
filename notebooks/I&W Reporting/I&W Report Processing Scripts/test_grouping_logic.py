#!/usr/bin/env python3
"""
Quick test script to verify grouping logic and check for duplicate reports.
"""

import pandas as pd
import sys
import os

# Add the scripts directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'scripts'))

def test_grouping_logic():
    """Test the grouping logic to see if we're creating duplicate reports."""
    
    # Create test data similar to what we'd get from the real pipeline
    test_data = pd.DataFrame({
        'search_term': ['192.168.1.1', '10.0.0.1', '172.16.1.1', '203.0.113.1'],
        'group_id': ['6755399443004631', '6755399443004631', pd.NA, pd.NA],
        'type': ['IP', 'IP', 'IP', 'IP'],
        'observed_date': ['2025-10-01', '2025-10-01', '2025-10-02', '2025-10-03']
    })
    
    print("Test DataFrame:")
    print(test_data)
    print("\nGroup_id info:")
    print(f"Total indicators: {len(test_data)}")
    print(f"Indicators with group_id: {test_data['group_id'].notna().sum()}")
    print(f"Unique group_ids: {list(test_data['group_id'].dropna().unique())}")
    
    # Simulate the grouping logic
    has_group = "group_id" in test_data.columns and test_data["group_id"].notna().any()
    
    created_reports = []
    
    if has_group:
        print("\nProcessing grouped reports...")
        # 1) One report per non-null group_id
        for gid, gdf in test_data.dropna(subset=["group_id"]).groupby("group_id", dropna=True):
            unique_indicators = list(gdf['search_term'].unique())
            print(f"Group {gid}: {len(gdf)} indicators: {unique_indicators}")
            
            if len(unique_indicators) == 1:
                base_name = unique_indicators[0]
                report_name = f"I&W_Report_{base_name}.docx"
                print(f"  -> Creating report: {report_name}")
            else:
                base_name = f"Group_{gid}"
                report_name = f"I&W_Report_{base_name}.docx"
                print(f"  -> Creating report: {report_name}")
            
            created_reports.append((report_name, unique_indicators))

        # 2) Orphans (no group_id) → one doc per indicator
        orphan_df = test_data[test_data["group_id"].isna()]
        if not orphan_df.empty and "search_term" in orphan_df.columns:
            orphan_indicators = list(orphan_df["search_term"].dropna().unique())
            print(f"\nProcessing orphaned indicators: {orphan_indicators}")
            for indicator in orphan_indicators:
                report_name = f"I&W_Report_{indicator}.docx"
                print(f"  -> Creating report: {report_name}")
                created_reports.append((report_name, [indicator]))
    
    print(f"\nTotal reports that would be created: {len(created_reports)}")
    for report_name, indicators in created_reports:
        print(f"  {report_name} -> {indicators}")
    
    # Check for duplicates
    all_indicators_in_reports = []
    for _, indicators in created_reports:
        all_indicators_in_reports.extend(indicators)
    
    original_indicators = set(test_data['search_term'].tolist())
    reported_indicators = set(all_indicators_in_reports)
    
    print(f"\nDuplication check:")
    print(f"Original indicators: {original_indicators}")
    print(f"Indicators in reports: {reported_indicators}")
    print(f"Duplicates? {len(all_indicators_in_reports) != len(set(all_indicators_in_reports))}")
    if len(all_indicators_in_reports) != len(set(all_indicators_in_reports)):
        from collections import Counter
        counts = Counter(all_indicators_in_reports)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        print(f"Duplicate indicators: {duplicates}")

if __name__ == "__main__":
    test_grouping_logic()