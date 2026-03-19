# Gacha Revenue Dashboard (Top 30)

An interactive Streamlit dashboard for exploring monthly **gacha game revenue** rankings (Top 30 per month), with filters and charts for quick comparison across games and scopes. 

Data source (as shown in-app): https://revenue.ennead.cc/revenue 

## Features
- Sidebar filters for `Scope` and optional `Games` selection. 
- KPI cards: number of games shown, total revenue for the latest month, and top game in the latest month. 
- Charts:
  - Horizontal bar chart of top games for a selected month. 
  - Line chart showing revenue trends across months (auto-limits to top games if none selected). 
- Data table view; missing values indicate the game did not make Top 30 for that month. 

## Project structure (suggested)
```text
.
├── code.py
├── requirements.txt
└── data.csv

```

## How to run

1) Create and activate a virtual environment (recommended)

```bash
python -m venv .venv
# macOS/Linux:
source .venv/bin/activate
# Windows:
# .venv\Scripts\activate
```
2) Install dependencies
```
pip install -r requirements.txt
```
3) Run the app
```
streamlit run code.py
```
