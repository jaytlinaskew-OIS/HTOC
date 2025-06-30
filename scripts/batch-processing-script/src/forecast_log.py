import pandas as pd
import os

def update_horizontal_forecast_log(production_df, actuals_df, log_csv_path):
    today = actuals_df['date'].max().normalize()
    col_name = f"Forecast Result: {today.strftime('%Y-%m-%d')}"
    records = {}

    for h in [7, 14, 30]:
        tag_col = f'Confidence: {h}-Day'
        target_date = today + pd.Timedelta(days=h)
        target_str = target_date.strftime('%Y-%m-%d')

        actuals_on_target = actuals_df[actuals_df['date'] == target_date][['indicator', 'seen']]
        actuals_map = dict(zip(actuals_on_target['indicator'], actuals_on_target['seen']))

        for _, row in production_df.iterrows():
            indicator = row['Indicator']
            forecast_tag = row[tag_col]
            was_seen = actuals_map.get(indicator, None)

            if target_date > today:
                outcome = "Pending"
            elif was_seen == 1:
                outcome = "Seen"
            elif was_seen == 0:
                outcome = "Missed"
            else:
                outcome = "Unknown"

            full_tag = f"{forecast_tag} -> {target_str} -> {outcome}"
            records[indicator] = records.get(indicator, '') + (f" | {full_tag}" if indicator in records else full_tag)

    new_col_df = pd.DataFrame.from_dict(records, orient='index', columns=[col_name])
    new_col_df.index.name = 'Indicator'
    new_col_df.reset_index(inplace=True)

    if os.path.exists(log_csv_path):
        existing = pd.read_csv(log_csv_path)

        def update_cell(cell, indicator):
            if not isinstance(cell, str) or '-> Pending' not in cell:
                return cell

            segments = cell.split(' | ')
            updated_segments = []

            for segment in segments:
                try:
                    parts = segment.split('->')
                    if len(parts) != 3:
                        updated_segments.append(segment)
                        continue

                    tag, target_str, status = [p.strip() for p in parts]
                    target_date = pd.to_datetime(target_str)

                    if target_date.date() == today.date() and status == 'Pending':
                        seen = actuals_df[
                            (actuals_df['indicator'] == indicator) &
                            (actuals_df['date'] == today)
                        ]['seen'].values
                        outcome = 'Seen' if len(seen) > 0 and seen[0] == 1 else 'Missed' if len(seen) > 0 else 'Unknown'
                        updated_segments.append(f"{tag} -> {target_str} -> {outcome}")
                    else:
                        updated_segments.append(segment)
                except:
                    updated_segments.append(segment)

            return ' | '.join(updated_segments)

        for col in existing.columns:
            if col.startswith("Forecast Result: "):
                existing[col] = existing.apply(lambda row: update_cell(row[col], row['Indicator']), axis=1)

        if col_name in existing.columns:
            existing.drop(columns=[col_name], inplace=True)

        merged = pd.merge(existing, new_col_df, on='Indicator', how='outer')
    else:
        merged = new_col_df

    forecast_cols = sorted(
        [col for col in merged.columns if col.startswith("Forecast Result: ")],
        reverse=True
    )
    recent_cols = forecast_cols[:30]
    final_cols = ['Indicator'] + sorted(recent_cols)
    merged = merged[final_cols]

    return merged