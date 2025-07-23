import baostock as bs
import pandas as pd
import os
from datetime import datetime
from tqdm import tqdm
import matplotlib
import matplotlib.pyplot as plt

matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'Arial Unicode MS']
matplotlib.rcParams['axes.unicode_minus'] = False

def download_quarterly_financials(stock_code: str, year: int, quarter: int, save_folder="output/financial_data") -> pd.DataFrame:
    def query_data(query_func, name, **kwargs):
        rs = query_func(**kwargs)
        if rs.error_code != '0':
            print(f"Error: {stock_code} - {year}Q{quarter} - {name} failed: {rs.error_msg}")
            return pd.DataFrame()
        data = []
        while rs.next():
            data.append(rs.get_row_data())
        return pd.DataFrame(data, columns=rs.fields)

    os.makedirs(save_folder, exist_ok=True)

    profit_df  = query_data(bs.query_profit_data,    "profitability", code=stock_code, year=year, quarter=quarter)
    op_df      = query_data(bs.query_operation_data, "operational",    code=stock_code, year=year, quarter=quarter)
    growth_df  = query_data(bs.query_growth_data,    "growth",         code=stock_code, year=year, quarter=quarter)
    balance_df = query_data(bs.query_balance_data,   "solvency",       code=stock_code, year=year, quarter=quarter)
    cash_df    = query_data(bs.query_cash_flow_data, "cashflow",       code=stock_code, year=year, quarter=quarter)
    dupont_df  = query_data(bs.query_dupont_data,    "dupont",         code=stock_code, year=year, quarter=quarter)

    def tag(df, prefix):
        return df.add_prefix(prefix + "_") if not df.empty else pd.DataFrame()

    merged = pd.concat([
        tag(profit_df,  "profit"),
        tag(op_df,      "operation"),
        tag(growth_df,  "growth"),
        tag(balance_df, "balance"),
        tag(cash_df,    "cash"),
        tag(dupont_df,  "dupont")
    ], axis=1)

    if merged.empty:
        return pd.DataFrame()

    if not profit_df.empty and "statDate" in profit_df.columns:
        merged["statDate"] = profit_df["statDate"]
    elif not op_df.empty and "statDate" in op_df.columns:
        merged["statDate"] = op_df["statDate"]
    else:
        merged["statDate"] = f"{year}Q{quarter}"

    filename = os.path.join(save_folder, f"{stock_code}_{year}_Q{quarter}.csv")
    merged.to_csv(filename, index=False, encoding="utf-8-sig")
    return merged

def batch_download_financials():
    stock_input = input("Enter stock codes separated by commas, or leave blank to use saved_stocks.txt: ").strip()
    if stock_input:
        stock_list = [
            s.strip().replace("_", ".").lower()
            for s in stock_input.split(",")
            if s.strip()
        ]
    else:
        saved_path = "analysis/saved_stocks.txt"
        if not os.path.exists(saved_path):
            print("Error: saved_stocks.txt not found.")
            return
        with open(saved_path, "r", encoding="utf-8") as f:
            stock_list = [line.strip() for line in f if line.strip()]
        if not stock_list:
            print("Warning: stock code file is empty.")
            return
        print(f"Loaded {len(stock_list)} stock codes.")

    def parse_quarter(qstr):
        try:
            y, q = int(qstr[:4]), int(qstr[-1])
            if 1 <= q <= 4:
                return y, q
        except:
            return None, None

    start_input = input("Enter start quarter (e.g. 2020Q1): ").strip().upper()
    end_input   = input("Enter end quarter (e.g. 2023Q4): ").strip().upper()
    sy, sq = parse_quarter(start_input)
    ey, eq = parse_quarter(end_input)
    if not (sy and sq and ey and eq) or (sy, sq) > (ey, eq):
        print("Error: invalid quarter range.")
        return

    quarters = []
    for y in range(sy, ey + 1):
        for q in range(1, 5):
            if (y == sy and q < sq) or (y == ey and q > eq):
                continue
            quarters.append((y, q))

    os.makedirs("output/financial_data", exist_ok=True)

    total_tasks = len(stock_list) * len(quarters)
    pbar = tqdm(total=total_tasks, desc="Downloading")
    success_quarters = 0
    success_stocks = 0

    for code in stock_list:
        for y, q in quarters:
            filename = f"{code}_{y}_Q{q}.csv"
            fpath = os.path.join("output", "financial_data", filename)

            if os.path.exists(fpath):
                try:
                    df_old = pd.read_csv(fpath)
                    if not df_old.empty:
                        pbar.update(1)
                        success_quarters += 1
                        continue
                except:
                    pass

            try:
                df = download_quarterly_financials(code, y, q)
                if df is not None and not df.empty:
                    success_quarters += 1
            except Exception as e:
                print(f"Error: {code} {y}Q{q} - {e}")
            pbar.update(1)

        try:
            merge_financial_quarters(code)
            success_stocks += 1
        except Exception as e:
            print(f"Warning: merge failed - {code} - {e}")

        try:
            clean_financial_dates(code)
            print(f"Saved to output/{code}_cleaned.csv")
        except Exception as e:
            print(f"Warning: failed to clean date - {code} - {e}")

    pbar.close()
    print(f"\nCompleted: {success_quarters} quarters downloaded.")
    print(f"{success_stocks} stock files merged and saved.")

def merge_financial_quarters(code: str, folder="output/financial_data"):
    files = [
        f for f in os.listdir(folder)
        if f.startswith(f"{code}_") and f.endswith(".csv")
    ]

    if not files:
        print(f"Warning: no quarterly files found for {code}")
        return

    dataframes = []
    for f in files:
        try:
            path = os.path.join(folder, f)
            df = pd.read_csv(path)
            if not df.empty:
                dataframes.append(df)
        except Exception as e:
            print(f"Warning: skipped corrupted file {f} - {e}")

    if not dataframes:
        print(f"Warning: all quarterly data invalid for {code}")
        return

    df_all = pd.concat(dataframes, ignore_index=True)

    if "statDate" in df_all.columns:
        try:
            df_all["statDate"] = pd.to_datetime(df_all["statDate"])
            df_all = df_all.sort_values("statDate")
        except Exception as e:
            print(f"Warning: sorting failed - {code} - {e}")
    else:
        print(f"Warning: no statDate found in {code}")

    merged_path = os.path.join(folder, f"{code}.csv")
    df_all.to_csv(merged_path, index=False, encoding="utf-8-sig")
    print(f"Merged file saved: {merged_path}")

def clean_financial_dates(code: str, input_folder="output/financial_data", output_folder="output"):
    input_path = os.path.join(input_folder, f"{code}.csv")
    if not os.path.exists(input_path):
        print(f"Error: file not found - {input_path}")
        return

    df = pd.read_csv(input_path)

    stat_cols = [col for col in df.columns if "statDate" in col]
    pub_cols = [col for col in df.columns if "pubDate" in col]

    stat_val = None
    for col in stat_cols:
        if df[col].notna().sum() > 0:
            stat_val = df[col]
            break

    pub_val = None
    for col in pub_cols:
        if df[col].notna().sum() > 0:
            pub_val = df[col]
            break

    if stat_val is not None:
        df["statDate"] = stat_val
    if pub_val is not None:
        df["pubDate"] = pub_val

    drop_cols = [col for col in stat_cols + pub_cols if col in df.columns and col not in ["statDate", "pubDate"]]
    df.drop(columns=drop_cols, inplace=True)

    new_cols = [c for c in ["statDate", "pubDate"] if c in df.columns]
    rest_cols = [c for c in df.columns if c not in new_cols]
    df = df[new_cols + rest_cols]

    os.makedirs(output_folder, exist_ok=True)
    output_path = os.path.join(output_folder, f"{code}_cleaned.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Cleaned file saved: {output_path}")


def search_and_save_stock_code(
    list_path="output/all_stocks.csv",
    save_path="analysis/saved_stocks.txt"
):
    if os.path.exists(list_path):
        ctime = os.path.getctime(list_path)
        readable_time = datetime.fromtimestamp(ctime).strftime("%Y-%m-%d %H:%M")
        print(f"Local stock list cache found: {list_path}")
        print(f"Last update time: {readable_time}")
        update_choice = input("Update stock list? (y/n): ").strip().lower()
        if update_choice == "y":
            print("Fetching full market stock list...")
            rs = bs.query_all_stock()
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            df = pd.DataFrame(data_list, columns=rs.fields)
            os.makedirs(os.path.dirname(list_path), exist_ok=True)
            df.to_csv(list_path, index=False, encoding="utf-8-sig")
            print(f"Stock list updated and saved to: {list_path}")
        else:
            print("Using local cached stock list.")
            df = pd.read_csv(list_path)
    else:
        print("No local stock list found. Fetching for the first time...")
        rs = bs.query_all_stock()
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        df = pd.DataFrame(data_list, columns=rs.fields)
        os.makedirs(os.path.dirname(list_path), exist_ok=True)
        df.to_csv(list_path, index=False, encoding="utf-8-sig")
        print(f"Stock list saved to: {list_path}")

    selected_codes = set()

    while True:
        keyword = input("\nEnter partial company name in Chinese (or 'q' to quit): ").strip()
        if keyword.lower() in ["q", "quit", "exit"]:
            break

        match_df = df[df["code_name"].str.contains(keyword)]
        if match_df.empty:
            print("No match found, try another keyword.")
            continue

        print("\nMatch results:")
        match_df = match_df.reset_index(drop=True)
        for idx, row in match_df.iterrows():
            print(f"{idx}. {row['code_name']} ({row['code']})")

        choice = input("Enter index(es) to save (e.g. 0,2,4), or press Enter to skip: ").strip()
        if choice:
            try:
                indexes = [int(x.strip()) for x in choice.split(",") if x.strip().isdigit()]
                added = []
                for i in indexes:
                    if 0 <= i < len(match_df):
                        code = match_df.loc[i, "code"]
                        selected_codes.add(code)
                        added.append(code)
                    else:
                        print(f"Index {i} out of range, ignored.")
                if added:
                    print(f"Temporarily saved {len(added)} codes: {', '.join(added)}")
                else:
                    print("No codes saved this round.")
            except Exception as e:
                print(f"Invalid input: {e}. No codes saved.")

    if selected_codes:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w", encoding="utf-8") as f:
            for code in sorted(set(selected_codes)):
                f.write(code.strip() + "\n")
        print(f"\nSaved {len(selected_codes)} stock codes to: {save_path}")
    else:
        print("\nNo stock codes selected. Nothing saved.")


def get_time_range_from_user(df):
    import pandas as pd

    available_start = df["statDate"].min()
    available_end = df["statDate"].max()

    def date_to_quarter(date_obj):
        year = date_obj.year
        quarter = (date_obj.month - 1) // 3 + 1
        return f"{year}Q{quarter}"

    def quarter_to_date(qstr):
        year = int(qstr[:4])
        q = int(qstr[-1])
        month_day = {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}[str(q)]
        return pd.to_datetime(f"{year}-{month_day}")

    print(f"\nAvailable data range: {date_to_quarter(available_start)} ~ {date_to_quarter(available_end)}")
    use_custom = input("Do you want to customize the time range? (y/n): ").strip().lower()

    if use_custom == "y":
        s_q = input("Enter start quarter (e.g. 2021Q1): ").strip().upper()
        e_q = input("Enter end quarter (e.g. 2024Q4): ").strip().upper()
        try:
            start_date = quarter_to_date(s_q)
            end_date = quarter_to_date(e_q)
        except:
            print("Invalid time format. Using default range.")
            start_date, end_date = available_start, available_end
    else:
        start_date, end_date = available_start, available_end

    return start_date, end_date


def function_plot_financial_metric(folder="output"):

    field_categories = {
        "Profitability": {
            "profit_roeAvg": ("ROE (%)", "Net Profit / Avg. Net Assets"),
            "profit_npMargin": ("Net Profit Margin (%)", "Net Profit / Revenue"),
            "profit_gpMargin": ("Gross Margin (%)", "Gross Profit / Revenue"),
            "profit_netProfit": ("Net Profit", "Total Profit - Tax"),
            "profit_epsTTM": ("EPS (Yuan)", "Net Profit / Total Shares"),
        },
        "Operational Efficiency": {
            "operation_NRTurnRatio": ("AR Turnover", "Net Sales / Avg. AR"),
            "operation_NRTurnDays": ("AR Turnover Days", "365 / AR Turnover"),
            "operation_INVTurnRatio": ("Inventory Turnover", "COGS / Avg. Inventory"),
            "operation_INVTurnDays": ("Inventory Turnover Days", "365 / Inventory Turnover"),
            "operation_CATurnRatio": ("Current Asset Turnover", "Revenue / Avg. Current Assets"),
            "operation_AssetTurnRatio": ("Total Asset Turnover", "Revenue / Avg. Total Assets"),
        },
        "Growth": {
            "growth_YOYEquity": ("Equity YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYAsset": ("Assets YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYNI": ("Net Profit YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYEPSBasic": ("EPS YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYPNI": ("Non-recurring Net Profit YoY (%)", "(Current - Prev) / Prev"),
        },
        "Solvency": {
            "balance_currentRatio": ("Current Ratio", "Current Assets / Current Liabilities"),
            "balance_quickRatio": ("Quick Ratio", "Quick Assets / Current Liabilities"),
            "balance_cashRatio": ("Cash Ratio", "Cash / Current Liabilities"),
            "balance_YOYLiability": ("Liability YoY", "(Current - Prev) / Prev"),
            "balance_liabilityToAsset": ("Debt-to-Asset Ratio", "Total Liabilities / Total Assets"),
            "balance_assetToEquity": ("Equity Multiplier", "Total Assets / Shareholder Equity"),
        },
        "Cash Flow": {
            "cash_CAToAsset": ("Current Assets / Total Assets", "Current Assets / Total Assets"),
            "cash_NCAToAsset": ("Non-Current Assets / Total", "Non-Current Assets / Total Assets"),
            "cash_tangibleAssetToAsset": ("Tangible / Total Assets", "Tangible Assets / Total"),
            "cash_ebitToInterest": ("EBIT / Interest", "EBIT / Interest Expense"),
            "cash_CFOToOR": ("Operating CF / Revenue", "Operating Cash Flow / Revenue"),
            "cash_CFOToNP": ("Operating CF / Net Profit", "OCF / Net Profit"),
            "cash_CFOToGr": ("Operating CF / Capex", "OCF / Capital Expenditure"),
        },
        "DuPont Analysis": {
            "dupont_dupontROE": ("DuPont ROE", "Net Profit / Equity"),
            "dupont_dupontAssetStoEquity": ("Equity Multiplier", "Assets / Equity"),
            "dupont_dupontAssetTurn": ("Asset Turnover", "Revenue / Assets"),
            "dupont_dupontPnitoni": ("Net Profit Margin", "Net Profit / Revenue"),
            "dupont_dupontNitogr": ("Net Margin", "Net Profit / Revenue"),
            "dupont_dupontTaxBurden": ("Tax Burden", "Net Profit / Pre-Tax Profit"),
            "dupont_dupontIntburden": ("Interest Burden", "Pre-Tax Profit / EBIT"),
            "dupont_dupontEbittogr": ("EBIT Margin", "EBIT / Revenue"),
        }
    }

    files = [f for f in os.listdir(folder) if f.endswith("_cleaned.csv")]
    if not files:
        print("No cleaned CSV files found in directory.")
        return

    print("\nAvailable stock files:")
    for idx, f in enumerate(files):
        print(f"{idx}. {f}")
    f_idx = input("Enter file index to plot: ").strip()
    if not f_idx.isdigit() or int(f_idx) >= len(files):
        print("Invalid index input.")
        return

    filename = files[int(f_idx)]
    filepath = os.path.join(folder, filename)
    code = filename.replace("_cleaned.csv", "")

    df = pd.read_csv(filepath)
    if "statDate" not in df.columns:
        print("statDate column not found in file.")
        return

    df["statDate"] = pd.to_datetime(df["statDate"], errors="coerce")
    df = df.dropna(subset=["statDate"])
    if df.empty:
        print("No valid statDate data.")
        return

    start_date, end_date = get_time_range_from_user(df)
    df = df[(df["statDate"] >= start_date) & (df["statDate"] <= end_date)].copy()

    while True:
        print("\nAvailable indicator categories:")
        categories = list(field_categories.keys())
        for i, cat in enumerate(categories):
            print(f"{i}. {cat}")
        cat_input = input("Select category index: ").strip()
        if not cat_input.isdigit() or int(cat_input) >= len(categories):
            print("Invalid category selection.")
            return
        selected_cat = categories[int(cat_input)]
        fields = field_categories[selected_cat]

        print(f"\nAvailable fields in {selected_cat}:")
        keys = list(fields.keys())
        for i, k in enumerate(keys):
            cname, _ = fields[k]
            print(f"{i}. {k} —— {cname}")
        field_input = input("Enter field index to plot: ").strip()
        if not field_input.isdigit() or int(field_input) >= len(keys):
            print("Invalid field index.")
            return
        field_key = keys[int(field_input)]
        field_label, field_formula = fields[field_key]
        if field_key not in df.columns:
            print(f"Field {field_key} not found in file.")
            return

        df_plot = df[["statDate", field_key]].dropna().sort_values("statDate")
        plt.figure(figsize=(16, 6))
        plt.plot(df_plot["statDate"], df_plot[field_key], marker='o', linestyle='-', label=code)
        for x, y in zip(df_plot["statDate"], df_plot[field_key]):
            if pd.notna(y):
                plt.text(x, y, f"{y:.2f}", fontsize=8, ha='center', va='bottom')

        plt.xlabel("Quarter", fontsize=12)
        plt.ylabel(field_label, fontsize=12)
        plt.xticks(df_plot["statDate"], rotation=45, fontsize=8)
        plt.yticks(fontsize=10)
        plt.suptitle(f"{field_label}", fontsize=16, fontweight="bold", y=0.96)
        plt.title(f"{field_key} · Formula: {field_formula}", fontsize=10, color="gray", pad=2)
        plt.legend(title="Stock Code", fontsize=9)
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.tight_layout(rect=[0.05, 0.05, 0.98, 0.90])

        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        save_choice = input("Save chart to local file? (y/n): ").strip().lower()
        if save_choice == "y":
            stock_name = code
            try:
                stock_file = os.path.join(project_root, "output", "all_stocks.csv")
                df_name = pd.read_csv(stock_file)
                match = df_name[df_name["code"] == code]
                if not match.empty:
                    stock_name = match.iloc[0]["code_name"]
            except:
                print("Unable to read stock name. Using code only.")

            output_dir = os.path.join(project_root, "output", "figure", f"{stock_name}_{code}")
            os.makedirs(output_dir, exist_ok=True)

            def date_to_quarter(date_obj):
                year = date_obj.year
                quarter = (date_obj.month - 1) // 3 + 1
                return f"{year}Q{quarter}"

            start_str = date_to_quarter(start_date)
            end_str = date_to_quarter(end_date)
            filename = f"{field_key}_{start_str}-{end_str}.png"
            save_path = os.path.join(output_dir, filename)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Chart saved to: {save_path}")
            plt.close()

        again = input("Plot another chart? (y/n): ").strip().lower()
        if again != "y":
            break

def function_plot_all_metrics(folder="output"):
    field_categories = {
        "Profitability": {
            "profit_roeAvg": ("ROE (%)", "Net Profit / Avg. Net Assets"),
            "profit_npMargin": ("Net Profit Margin (%)", "Net Profit / Revenue"),
            "profit_gpMargin": ("Gross Margin (%)", "Gross Profit / Revenue"),
            "profit_netProfit": ("Net Profit", "Total Profit - Tax"),
            "profit_epsTTM": ("EPS (Yuan)", "Net Profit / Total Shares"),
        },
        "Operational Efficiency": {
            "operation_NRTurnRatio": ("AR Turnover", "Net Sales / Avg. AR"),
            "operation_NRTurnDays": ("AR Turnover Days", "365 / AR Turnover"),
            "operation_INVTurnRatio": ("Inventory Turnover", "COGS / Avg. Inventory"),
            "operation_INVTurnDays": ("Inventory Turnover Days", "365 / Inventory Turnover"),
            "operation_CATurnRatio": ("Current Asset Turnover", "Revenue / Avg. Current Assets"),
            "operation_AssetTurnRatio": ("Total Asset Turnover", "Revenue / Avg. Total Assets"),
        },
        "Growth": {
            "growth_YOYEquity": ("Equity YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYAsset": ("Assets YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYNI": ("Net Profit YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYEPSBasic": ("EPS YoY (%)", "(Current - Prev) / Prev"),
            "growth_YOYPNI": ("Non-recurring Net Profit YoY (%)", "(Current - Prev) / Prev"),
        },
        "Solvency": {
            "balance_currentRatio": ("Current Ratio", "Current Assets / Current Liabilities"),
            "balance_quickRatio": ("Quick Ratio", "Quick Assets / Current Liabilities"),
            "balance_cashRatio": ("Cash Ratio", "Cash / Current Liabilities"),
            "balance_YOYLiability": ("Liability YoY", "(Current - Prev) / Prev"),
            "balance_liabilityToAsset": ("Debt-to-Asset Ratio", "Total Liabilities / Total Assets"),
            "balance_assetToEquity": ("Equity Multiplier", "Total Assets / Equity"),
        },
        "Cash Flow": {
            "cash_CAToAsset": ("Current Assets / Total Assets", "Current Assets / Total Assets"),
            "cash_NCAToAsset": ("Non-Current Assets / Total", "Non-Current Assets / Total Assets"),
            "cash_tangibleAssetToAsset": ("Tangible / Total Assets", "Tangible Assets / Total"),
            "cash_ebitToInterest": ("EBIT / Interest", "EBIT / Interest Expense"),
            "cash_CFOToOR": ("Operating CF / Revenue", "OCF / Revenue"),
            "cash_CFOToNP": ("Operating CF / Net Profit", "OCF / Net Profit"),
            "cash_CFOToGr": ("Operating CF / Capex", "OCF / Capital Expenditure"),
        },
        "DuPont Analysis": {
            "dupont_dupontROE": ("DuPont ROE", "Net Profit / Equity"),
            "dupont_dupontAssetStoEquity": ("Equity Multiplier", "Assets / Equity"),
            "dupont_dupontAssetTurn": ("Asset Turnover", "Revenue / Assets"),
            "dupont_dupontPnitoni": ("Net Profit Margin", "Net Profit / Revenue"),
            "dupont_dupontNitogr": ("Net Margin", "Net Profit / Revenue"),
            "dupont_dupontTaxBurden": ("Tax Burden", "Net Profit / Pre-Tax Profit"),
            "dupont_dupontIntburden": ("Interest Burden", "Pre-Tax Profit / EBIT"),
            "dupont_dupontEbittogr": ("EBIT Margin", "EBIT / Revenue"),
        }
    }

    files = [f for f in os.listdir(folder) if f.endswith("_cleaned.csv")]
    if not files:
        print("No cleaned CSV files found.")
        return

    print("\nAvailable stocks:")
    for idx, f in enumerate(files):
        print(f"{idx}. {f}")
    f_idx = input("Enter file index to plot: ").strip()
    if not f_idx.isdigit() or int(f_idx) >= len(files):
        print("Invalid input.")
        return

    filename = files[int(f_idx)]
    filepath = os.path.join(folder, filename)
    code = filename.replace("_cleaned.csv", "")

    df = pd.read_csv(filepath)
    df["statDate"] = pd.to_datetime(df["statDate"], errors="coerce")
    df = df.dropna(subset=["statDate"])
    if df.empty:
        print("No valid statDate found.")
        return

    start_date, end_date = get_time_range_from_user(df)
    df = df[(df["statDate"] >= start_date) & (df["statDate"] <= end_date)].copy()

    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    stock_name = code
    try:
        df_name = pd.read_csv(os.path.join(project_root, "output", "all_stocks.csv"))
        match = df_name[df_name["code"] == code]
        if not match.empty:
            stock_name = match.iloc[0]["code_name"]
    except:
        pass

    output_dir = os.path.join(project_root, "output", "figure", f"{stock_name}_{code}")
    os.makedirs(output_dir, exist_ok=True)

    def date_to_quarter(date_obj):
        year = date_obj.year
        quarter = (date_obj.month - 1) // 3 + 1
        return f"{year}Q{quarter}"

    start_str = date_to_quarter(start_date)
    end_str = date_to_quarter(end_date)

    print(f"\nGenerating charts and saving to: {output_dir}")

    for category, fields in field_categories.items():
        for field_key, (field_label, field_formula) in fields.items():
            if field_key not in df.columns:
                continue
            df_plot = df[["statDate", field_key]].dropna().sort_values("statDate")
            if df_plot.empty:
                continue

            plt.figure(figsize=(10, 5))
            plt.plot(df_plot["statDate"], df_plot[field_key], marker='o', linestyle='-', label=code)
            plt.xlabel("Quarter", fontsize=12)
            plt.ylabel(field_label, fontsize=12)
            plt.xticks(rotation=45)
            plt.suptitle(f"{field_label}", fontsize=14, fontweight="bold", y=0.97)
            plt.title(f"{field_key} · Formula: {field_formula}", fontsize=10, color="gray", pad=2)
            plt.legend(title="Stock Code")
            plt.grid(True)
            plt.tight_layout(rect=[0.07, 0.07, 0.985, 0.92])

            filename = f"{field_key}_{start_str}-{end_str}.png"
            save_path = os.path.join(output_dir, filename)
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            plt.close()

            print(f"Saved: {filename}")

    print("All charts generated successfully.")
