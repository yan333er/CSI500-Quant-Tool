
CSI500 Quant Tool
=============================================

Intro
--------------------

CSI500 Quant Tool is a fully modular and interactive Python application I designed to automate stock screening and financial analysis based on China’s CSI 500 Index. The system integrates historical price tracking, quarterly financial parsing, and multi-indicator charting into a command-line interface.

Built entirely from scratch, the tool supports:

- Batch data collection for over 500 listed stocks,
- Custom screening logic (e.g., limit-up/down tracking, top gainers),
- Quarterly financial processing with indicator categorization,
- Auto-generated charts with formula explanations and export functions.

As a demonstration, the current dataset includes real data for the entire CSI 500 as of July 23, 2025, with a special focus on Hengtong Optic-Electric (sh.600487), which I had previously researched during my equity research internship at Kaiyuan Securities. This stock was selected to replicate my prior analysis, with its cleaned data and financial charts included in the /financial_data/ and /figure/ folders.

This tool is not only a personal analysis assistant, but also the foundation for a future system that may include professional-grade stock classification, valuation models, and adaptive strategy testing based on updated market data.

=============================================

Main Menu (Main.py)
--------------------

1. Download or update stock data
   - Access historical price management
   - Module path: crawler/stock_price.py

2. Stock screening and financial analysis
   - Includes limit-up/down filters, financial data download, and charting
   - Module path: analysis/

0. Exit program

Data Download Menu
--------------------

- Incremental Update:
  Update existing files in daily_data_history/ to the latest date

- Refresh CSI 500 List:
  Download latest list to output/zz500_list.csv

- Full History Download:
  Specify date range to download all stock data (time-consuming)

Stock Screening Menu
--------------------

- Limit-Up/Down Filter:
  Identify stocks with daily price limits in recent N days; exportable report

- Top Gainers:
  Rank top stocks with highest single-day gain in the last N days

- Stock Code Lookup by Name:
  Search by partial Chinese name; save selected codes to analysis/saved_stocks.txt

Financial Data Menu
--------------------

- Download Single Quarter:
  Retrieve 6 categories of financials for a specific stock and quarter

- Batch Download:
  Download data for multiple stocks and quarters via saved_stocks.txt

- Interactive Plotting:
  Choose stock → category → indicator; charts saved in output/figure/

- Auto Charting:
  Plot all metrics silently and save by stock and category

=============================================

Structure
--------------------

CSI500_Quant_Tool/

├── Main.py                 -> Main interactive entry (menu system)
├── crawler/
│   └── stock_price.py          -> CSI 500 list & price data fetching
├── analysis/
│   ├── stock_search.py         -> Limit-up/down & gainers filtering
│   └── stock_analysis.py       -> Financial data download & plotting
├── output/
│   ├── financial_data/                    -> Cleaned quarterly financial data (e.g. sh.600487_cleaned.csv)
│   ├── figure/                            -> Auto-generated financial charts (saved by stock code)
│   ├── all_stocks.csv                     -> Full metadata of CSI 500 stocks (code, name, industry, etc.)
│   ├── zz500_list.csv                     -> Raw CSI 500 constituent list (latest snapshot)
│   ├── limit_up_stats_2025-06-12_2025-07-23.csv   -> Filtered limit-up stocks over date range
│   ├── limit_down_stats_2025-06-12_2025-07-23.csv -> Filtered limit-down stocks over date range
│   ├── top_single_day_gainers_30.csv      -> One-day top gainers with max increase in past 30 days
│   ├── sh.600487_cleaned.csv              -> Sample financial data for Hengtong Optoelectronics
├── daily_data_history/         -> Saved historical price CSVs
└── analysis/saved_stocks.txt   -> Selected stock codes (saved locally)

=============================================

Installation
--------------------

1. Make sure Python 3.8+ is installed.

2. Install required packages:
   pip install baostock pandas matplotlib tqdm

3. Run the tool:

=============================================

Acknowledgements
----------------

- This project was created to support my personal investment research using real Chinese A-share data.
- It was fully developed in Python, integrating data crawling, logic design, and visualization.
- Many parts of the code were generated with the help of ChatGPT, but all logic and structure were reviewed and modified by myself.
- All financial data is sourced via baostock (http://www.baostock.com/).
- Chart outputs and reports are generated based on stocks I've studied, including Hengtong Optoelectronics.

=============================================

Future Development
------------------

I plan to extend this tool into a more intelligent stock classification and valuation system. The next-stage roadmap includes:

- Scoring-based stock categorization (e.g., high-quality, stable, speculative, or junk)
- Valuation metrics such as PB/PE percentiles and ROE trend analysis
- Sell signal suggestions based on technical and fundamental indicators
- Strategy backtesting modules with automated performance tracking
- Scheduled data updates and classification history logging

These features are currently under planning and will be developed incrementally to better support my personal investment strategies.

The system is fully modular and may be extended for broader use cases. Collaboration is Extremely welcome!


Copyright © 2025 Mingxu Yan.
Open-source for learning and research purposes. Feel free to use with attribution.
