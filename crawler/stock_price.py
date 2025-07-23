import baostock as bs
import pandas as pd
import os
import time
import matplotlib.pyplot as plt
import matplotlib







matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei']  
matplotlib.rcParams['axes.unicode_minus'] = False  


def get_price_data_baostock(stock_code: str, start_date: str, end_date: str) -> pd.DataFrame:
    """
    Use Baostock to get A-share daily market data (forward adjusted)
    Parameters:
        stock_code: Stock code (format like 'sh.600000')
        start_date: Start date (format '2023-07-01')
        end_date: End date (format '2025-07-14')
    Returns:
        pd.DataFrame with fields: date, open, close, high, low, volume, code
    """

    rs = bs.query_history_k_data_plus(
        stock_code,
        "date,code,open,high,low,close,volume",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="2"  
    )

    data_list = []
    while rs.next():
        data_list.append(rs.get_row_data())

    df = pd.DataFrame(data_list, columns=rs.fields)

    
    df["open"] = pd.to_numeric(df["open"], errors='coerce')
    df["high"] = pd.to_numeric(df["high"], errors='coerce')
    df["low"] = pd.to_numeric(df["low"], errors='coerce')
    df["close"] = pd.to_numeric(df["close"], errors='coerce')
    df["volume"] = pd.to_numeric(df["volume"], errors='coerce')

    df = df.rename(columns={"code": "stock_code"})
    return df.sort_values(by="date").reset_index(drop=True)


def save_price_data_to_csv(df: pd.DataFrame, stock_code: str) -> str:
    """
    Save DataFrame as a CSV file (Path: daily_data/{stock_code}.csv)
    """
    output_dir = os.path.join(os.getcwd(), "daily_data_history")
    os.makedirs(output_dir, exist_ok=True)

    file_path = os.path.join(output_dir, f"{stock_code.replace('.', '_')}.csv")
    
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ {stock_code} data has been saved to {file_path}")
    return file_path


def get_zz500_stocks() -> pd.DataFrame:
    """
    Get all constituent stocks of CSI 500 index (update frequency: every Monday)
    Returns DataFrame with fields:
        code (e.g., 'sh.600519'), code_name, ...
    """
    lg = bs.login()
    if lg.error_code != "0":
        print("Login failed:", lg.error_msg)
        return pd.DataFrame()

    rs = bs.query_zz500_stocks()
    if rs.error_code != "0":
        print("Request failed:", rs.error_msg)
        bs.logout()
        return pd.DataFrame()

    data = []
    while rs.next():
        data.append(rs.get_row_data())

    bs.logout()
    df = pd.DataFrame(data, columns=rs.fields)
    return df


def fetch_and_save_zz500_list(output_path="output/zz500_list.csv") -> pd.DataFrame:
    """Fetch CSI 500 list and save as CSV"""
    df = get_zz500_stocks()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"✅ Fetched {len(df)} CSI 500 stocks and saved to: {output_path}")
    return df


def parse_stock_list(df: pd.DataFrame) -> tuple[list, dict, dict]:
    """
    Parse DataFrame and return:
    - List of stock codes (e.g., ['sh.600000', ...])
    - Name → Code mapping
    - Code → Name mapping
    """
    stock_code_list = []
    name_code_map = {}
    stock_dic = {}

    for _, row in df.iterrows():
        name = row["code_name"]
        code = row["code"]
        stock_code_list.append(code)
        name_code_map[name] = code
        stock_dic[code] = name

    print(f"✅ Successfully parsed stock data, total {len(stock_code_list)} stocks")
    return stock_code_list, name_code_map, stock_dic


def save_price_data_with_name(df: pd.DataFrame, stock_code: str, stock_dic: dict) -> str:
    """
    Save DataFrame as a CSV file (with company name), format: CompanyName_Code.csv
    If name mapping is not found, save as Code.csv only
    """
    output_dir = os.path.join(os.getcwd(), "daily_data_history")
    os.makedirs(output_dir, exist_ok=True)

    
    stock_name = stock_dic.get(stock_code, "Unknown").replace("/", "_").replace("\\", "_")

    
    filename = f"{stock_name}_{stock_code.replace('.', '_')}.csv"
    file_path = os.path.join(output_dir, filename)

    
    df.to_csv(file_path, index=False, encoding="utf-8-sig")
    print(f"✅ {stock_code} ({stock_name}) data has been saved to {file_path}")
    return file_path


def download_all_stock_data(stock_code_list: list, stock_dic: dict, start_date: str, end_date: str):
    """
    Batch download all stock daily data and save locally (with progress bar and company name)
    """
    total = len(stock_code_list)
    bar_length = 30

    for idx, code in enumerate(stock_code_list):
        try:
            df = get_price_data_baostock(code, start_date, end_date)
            if df.empty:
                print(f"⚠️ {code} has no data, skipping")
                continue
            save_price_data_with_name(df, code, stock_dic)
        except Exception as e:
            print(f"❌ Download failed: {code}, Error: {e}")
            continue

        
        progress = (idx + 1) / total
        filled = int(bar_length * progress)
        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"\r📊 Download progress: [{bar}] {idx + 1}/{total}", end="")

        time.sleep(0.1)  

    print("\n✅ All stock data download completed")


def find_top_gainers(data_folder="daily_data_history", recent_days=30, top_n=10):
    results = []

    for filename in os.listdir(data_folder):
        if filename.endswith(".csv"):
            filepath = os.path.join(data_folder, filename)
            try:
                df = pd.read_csv(filepath)
                df = df.sort_values("date")  

                if len(df) < recent_days + 1:
                    continue  

                
                recent_df = df[-(recent_days+1):].reset_index(drop=True)
                start_price = recent_df.loc[0, "close"]
                end_price = recent_df.loc[recent_days, "close"]

                if pd.isna(start_price) or pd.isna(end_price) or start_price == 0:
                    continue

                change = (end_price - start_price) / start_price

                results.append({
                    "Stock": filename.replace(".csv", ""),
                    "Start Price": round(start_price, 2),
                    "End Price": round(end_price, 2),
                    "Change %": round(change * 100, 2)
                })

            except Exception as e:
                print(f"❌ Failed to read: {filename}, Error: {e}")

    
    sorted_results = sorted(results, key=lambda x: x["Change %"], reverse=True)
    top_gainers = sorted_results[:top_n]
    top_df = pd.DataFrame(top_gainers)

    
    os.makedirs("output", exist_ok=True)
    top_df.to_excel("output/top_gainers.xlsx", index=False)
    print("✅ Analysis completed. Top 10 saved to output/top_gainers.xlsx")

    return top_df



def ensure_zz500_list(filepath="output/zz500_list.csv") -> tuple[list, dict, dict]:

    if not os.path.exists(filepath):
        print("⚠️ CSI 500 list not found, fetching......")
        df = fetch_and_save_zz500_list(filepath)
    else:
        df = pd.read_csv(filepath)
    return parse_stock_list(df)




def update_existing_stock_data(stock_code_list: list, stock_dic: dict, end_date: str, data_folder="daily_data_history"):

    total = len(stock_code_list)
    bar_length = 30
    updated_count = 0

    for idx, code in enumerate(stock_code_list):
        filename_part = code.replace(".", "_")
        match_files = [f for f in os.listdir(data_folder) if filename_part in f and f.endswith(".csv")]
        if not match_files:
            print(f"⚠️ Local file not found, skipping：{code}")
            continue

        filepath = os.path.join(data_folder, match_files[0])
        try:
            old_df = pd.read_csv(filepath)
            last_date = old_df['date'].max()
            start_date = pd.to_datetime(last_date) + pd.Timedelta(days=1)
            start_date_str = start_date.strftime("%Y-%m-%d")

            if start_date_str > end_date:
                continue  

            new_df = get_price_data_baostock(code, start_date_str, end_date)
            if new_df.empty:
                continue

            combined_df = pd.concat([old_df, new_df], ignore_index=True).drop_duplicates(subset="date")
            combined_df.to_csv(filepath, index=False, encoding="utf-8-sig")
            updated_count += 1
        except Exception as e:
            print(f"❌ Update failed：{code}，错误：{e}")

        
        progress = (idx + 1) / total
        filled = int(bar_length * progress)
        bar = "█" * filled + "-" * (bar_length - filled)
        print(f"\r📊 Update progress：[{bar}] {idx + 1}/{total}", end="")

    print(f"\n✅ Update completed, total updated {updated_count} stocks")










