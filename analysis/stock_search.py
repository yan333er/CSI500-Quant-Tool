import os
import pandas as pd

def filter_limit_up(data_folder="daily_data_history", threshold=0.098):
    days_input = input("Enter number of days to check (default 30): ").strip()
    threshold_input = input("Enter limit-up threshold as decimal (default 0.098): ").strip()
    threshold = float(threshold_input) if threshold_input else threshold
    recent_days = int(days_input) if days_input.isdigit() else 30

    results = []

    for filename in os.listdir(data_folder):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_folder, filename)
            try:
                df = pd.read_csv(filepath).sort_values("date").reset_index(drop=True)
                if len(df) < recent_days:
                    continue

                df_recent = df[-recent_days:].copy()
                df_recent["pct_chg"] = (df_recent["close"] - df_recent["open"]) / df_recent["open"]
                df_recent["is_limit_up"] = df_recent["pct_chg"] >= threshold

                limit_df = df_recent[df_recent["is_limit_up"]]
                if len(limit_df) == 0:
                    continue

                stock_name = filename.replace(".csv", "")
                limit_dates = limit_df["date"].tolist()
                pct_list = [round(p * 100, 2) for p in limit_df["pct_chg"]]

                results.append({
                    "Stock Name": stock_name,
                    "Limit-Up Count": len(limit_dates),
                    "Limit-Up Dates": limit_dates,
                    "Limit-Up Percentage List": pct_list
                })

            except Exception as e:
                print(f"Failed to read {filename}, Error: {e}")
                continue

    df_result = pd.DataFrame(results)
    df_result = df_result.sort_values("Limit-Up Count", ascending=False).reset_index(drop=True)

    if not df_result.empty:
        confirm = input("Save results to CSV file? (y/n): ").strip().lower()
        if confirm == "y":
            os.makedirs("output", exist_ok=True)
            start_date = df_recent["date"].min()
            end_date = df_recent["date"].max()
            filename = f"limit_up_stats_{start_date}_{end_date}.csv"
            save_path = os.path.join("output", filename)
            df_result.to_csv(save_path, index=False, encoding="utf-8-sig")
            print(f"Results saved to: {save_path}")
        else:
            print("Results not saved. Display only.")
    else:
        print("No limit-up stocks found. No file generated.")

    return df_result


def filter_limit_down(data_folder="daily_data_history", threshold=-0.098):
    days_input = input("Enter number of days to check (default 30): ").strip()
    threshold_input = input("Enter limit-down threshold (e.g. -0.098): ").strip()
    threshold = float(threshold_input) if threshold_input else threshold
    recent_days = int(days_input) if days_input.isdigit() else 30

    results = []

    for filename in os.listdir(data_folder):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_folder, filename)
            try:
                df = pd.read_csv(filepath).sort_values("date").reset_index(drop=True)
                if len(df) < recent_days:
                    continue

                df_recent = df[-recent_days:].copy()
                df_recent["pct_chg"] = (df_recent["close"] - df_recent["open"]) / df_recent["open"]
                df_recent["is_limit_down"] = df_recent["pct_chg"] <= threshold

                limit_df = df_recent[df_recent["is_limit_down"]]
                if len(limit_df) == 0:
                    continue

                stock_name = filename.replace(".csv", "")
                limit_dates = limit_df["date"].tolist()
                pct_list = [round(p * 100, 2) for p in limit_df["pct_chg"]]

                results.append({
                    "Stock Name": stock_name,
                    "Limit-Down Count": len(limit_dates),
                    "Limit-Down Dates": limit_dates,
                    "Limit-Down Percentage List": pct_list
                })

            except Exception as e:
                print(f"Failed to read {filename}, Error: {e}")
                continue

    df_result = pd.DataFrame(results)
    df_result = df_result.sort_values("Limit-Down Count", ascending=False).reset_index(drop=True)

    if not df_result.empty:
        confirm = input("Save results to CSV file? (y/n): ").strip().lower()
        if confirm == "y":
            os.makedirs("output", exist_ok=True)
            start_date = df_recent["date"].min()
            end_date = df_recent["date"].max()
            filename = f"limit_down_stats_{start_date}_{end_date}.csv"
            save_path = os.path.join("output", filename)
            df_result.to_csv(save_path, index=False, encoding="utf-8-sig")
            print(f"Results saved to: {save_path}")
        else:
            print("Results not saved. Display only.")
    else:
        print("No limit-down stocks found. No file generated.")

    return df_result

def filter_top_gainers(data_folder="daily_data_history", recent_days=30, top_n=10):
    results = []

    for filename in os.listdir(data_folder):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_folder, filename)
            try:
                df = pd.read_csv(filepath).sort_values("date").reset_index(drop=True)
                if len(df) < 1:
                    continue
                recent_df = df[-recent_days:].copy()
                recent_df["change_pct"] = (recent_df["close"] - recent_df["open"]) / recent_df["open"] * 100

                max_row = recent_df.loc[recent_df["change_pct"].idxmax()]
                results.append({
                    "Stock": filename.replace(".csv", ""),
                    "Date": max_row["date"],
                    "Open": round(max_row["open"], 2),
                    "Close": round(max_row["close"], 2),
                    "Change %": round(max_row["change_pct"], 2)
                })
            except Exception as e:
                print(f"{filename} failed to read, Error: {e}")

    sorted_results = sorted(results, key=lambda x: x["Change %"], reverse=True)
    for i, item in enumerate(sorted_results[:top_n]):
        item["Rank"] = i + 1

    df_top = pd.DataFrame(sorted_results[:top_n])

    confirm = input(f"Save Top {top_n} results as CSV? (y/n): ").strip().lower()
    if confirm == "y":
        os.makedirs("output", exist_ok=True)
        save_path = os.path.join("output", f"top_single_day_gainers_{top_n}.csv")
        df_top.to_csv(save_path, index=False, encoding="utf-8-sig")
        print(f"Saved to: {save_path}")

    return df_top
