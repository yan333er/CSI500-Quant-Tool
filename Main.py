
from crawler.stock_price import (
    fetch_and_save_zz500_list,
    parse_stock_list,
    download_all_stock_data,
    find_top_gainers,
    update_existing_stock_data,
    ensure_zz500_list,
)

from analysis.stock_search import (
    filter_limit_up,
    filter_limit_down,
    filter_top_gainers,
)

from analysis.stock_analysis import (
    download_quarterly_financials,
    batch_download_financials,
    search_and_save_stock_code,
    function_plot_financial_metric,
    function_plot_all_metrics
)

import pandas as pd
import os
from datetime import datetime
import baostock as bs


def function_download_history():
    while True:
        print("\nData Download & Update Menu")
        today_str = datetime.today().strftime("%Y-%m-%d")

        print("\nPlease select task type:")
        print("1. Update existing stock data (incremental)")
        print("2. Refresh CSI 500 stock list only")
        print("3. Download full historical stock data (may take long)")
        print("0. Return to previous menu")

        sub_choice = input("Enter your choice (0–3): ").strip()

        if sub_choice == "1":
            stock_code_list, name_code_map, stock_dic = ensure_zz500_list()
            print(f"Update to latest date? (default {today_str})")
            confirm = input("Continue? (y/n): ").strip().lower()
            if confirm != "y":
                print("Update canceled.")
                continue
            update_existing_stock_data(stock_code_list, stock_dic, today_str)

        elif sub_choice == "2":
            end = input(f"Enter end date (YYYY-MM-DD, default {today_str}): ").strip()
            end_date = end if end else today_str
            fetch_and_save_zz500_list()
            print(f"CSI 500 list updated (as of {end_date}).")

        elif sub_choice == "3":
            print("Enter time range (default last 2 years):")
            start = input("Start date (YYYY-MM-DD, default 2022-07-01): ").strip()
            end = input(f"End date (YYYY-MM-DD, default {today_str}): ").strip()
            start_date = start if start else "2022-07-01"
            end_date = end if end else today_str
            confirm = input("This may take a while. Continue? (y/n): ").strip().lower()
            if confirm != "y":
                print("Download canceled.")
                continue
            stock_code_list, name_code_map, stock_dic = ensure_zz500_list()
            download_all_stock_data(stock_code_list, stock_dic, start_date, end_date)
            print("All data downloaded successfully.")

        elif sub_choice == "0":
            print("Returning to main menu...")
            break

        else:
            print("Invalid input. Please enter a number between 0 and 3.")


def function_analysis_menu():
    while True:
        print("\nStock Analysis & Screening Menu")
        print("1. Screen stocks by conditions")
        print("2. Financial data analysis and plotting")
        print("3. Search stock code by name")
        print("0. Return to main menu")

        choice = input("Enter your choice (0–2): ").strip()

        if choice == "1":
            function_stock_filter_menu()

        elif choice == "2":
            function_financial_data_menu()

        elif choice == "3":
            search_and_save_stock_code()

        elif choice == "0":
            print("Returning to main menu")
            break

        else:
            print("Invalid input. Please try again.")


def function_stock_filter_menu():
    while True:
        print("\nStock Filter Menu")
        print("1. Filter continuous limit-up stocks")
        print("2. Filter continuous limit-down stocks")
        print("3. Top N gainers (based on min→max range)")
        print("0. Return to previous menu")

        choice = input("Enter your choice (0–3): ").strip()

        if choice == "1":
            df = filter_limit_up()
            print("\nLimit-up filter result:")
            print(df)

        elif choice == "2":
            df = filter_limit_down()
            print("\nLimit-down filter result:")
            print(df)

        elif choice == "3":
            days_input = input("Days to analyze (default 30): ").strip()
            topn_input = input("Show top N (default 10): ").strip()
            days = int(days_input) if days_input.isdigit() else 30
            top_n = int(topn_input) if topn_input.isdigit() else 10
            df = filter_top_gainers(recent_days=days, top_n=top_n)
            print(f"Top {top_n} gainers in last {days} days:")
            print(df)

        elif choice == "0":
            print("Returning to previous menu")
            break

        else:
            print("Invalid input. Please try again.")


def function_financial_data_menu():
    while True:
        print("\nFinancial Data Menu")
        print("1. Download financial data for one stock and quarter")
        print("2. Batch download for multiple stocks and quarters")
        print("3. Manually plot financial metrics")
        print("4. Automatically plot all categorized metrics")
        print("0. Return to previous menu")

        choice = input("Enter your choice (0–4): ").strip()

        if choice == "1":
            stock_code = input("Enter stock code (e.g., sh.600000): ").strip()
            year_input = input("Enter year (e.g., 2023): ").strip()
            quarter_input = input("Enter quarter (1–4): ").strip()

            if not stock_code or not year_input.isdigit() or quarter_input not in ["1", "2", "3", "4"]:
                print("Invalid input. Please try again.")
                continue

            year = int(year_input)
            quarter = int(quarter_input)
            download_quarterly_financials(stock_code, year, quarter)

        elif choice == "2":
            batch_download_financials()

        elif choice == "3":
            function_plot_financial_metric()

        elif choice == "4":
            function_plot_all_metrics()

        elif choice == "0":
            print("Returning to previous menu")
            break

        else:
            print("Invalid input. Please try again.")


def main_menu():
    bs.login()
    try:
        while True:
            print("\nWelcome to CSI500 Quant Tool")
            print("1. Download or update stock data")
            print("2. Stock analysis and screening")
            print("0. Exit program")

            choice = input("Enter your choice (0–2): ").strip()

            if choice == "1":
                function_download_history()

            elif choice == "2":
                function_analysis_menu()

            elif choice == "0":
                print("Exiting program. Goodbye!")
                break

            else:
                print("Invalid input. Please enter a number between 0 and 2.")
    finally:
        bs.logout()


if __name__ == "__main__":
    main_menu()
