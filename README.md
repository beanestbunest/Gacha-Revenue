# Gacha Revenue Dashboard (Top 30)

An interactive Streamlit dashboard for exploring monthly **gacha game revenue** rankings (Top 30 per month), with filters and charts for quick comparison across games and scopes. [file:1]

Data source (as shown in-app): https://revenue.ennead.cc/revenue [file:1]

## Features

- Sidebar filters for `Scope` and optional `Games` selection. [file:1]
- KPI cards: number of games shown, total revenue for the latest month, and top game in the latest month. [file:1]
- Charts:
  - Horizontal bar chart of top games for a selected month.
  - Line chart showing revenue trends across months (auto-limits to top games if none selected). [file:1]
- Data table view with missing values indicating the game did not make Top 30 for that month. [file:1]

## Project structure (suggested)

```text
.
├── gacha_rev_oct-jan_top_30.csv
└── (code folder)
    └── gacha_rev.py

Ensure the following packages are installed: pandas, plotly, streamlit
Run the following in the terminal: streamlit run gacha_rev.py
