import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Gacha Revenue (Top 30)", layout="wide")


# ----------------------------
# Data loading / cleaning
# ----------------------------
@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path, na_values=["N.A.", "NA", "N/A", "-"])

    month_cols = ["Oct", "Nov", "Dec", "Jan"]

    # Ensure required columns exist
    required = ["Game", "Scope"] + month_cols
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Missing columns in CSV: {missing}. Found: {df.columns.tolist()}")

    def money_to_float(x):
        if pd.isna(x):
            return None
        s = str(x).strip()
        if s.upper() in {"N.A.", "NA", "N/A", "-", ""}:
            return None

        # Remove $ and commas and other non-numeric chars (keeps dots)
        s = re.sub(r"[^0-9.]", "", s)

        # Handle OCR/placeholder weirdness like '.', '..', '...'
        if s == "" or set(s) == {"."}:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    for c in month_cols:
        df[c + "_num"] = df[c].apply(money_to_float)

    return df, month_cols


def month_order_cat(series: pd.Series, month_cols):
    return pd.Categorical(series, categories=month_cols, ordered=True)


# ----------------------------
# App UI
# ----------------------------
st.title("Gacha Revenue Dashboard (Top 30 per Month)") 
st.markdown("Data taken from https://revenue.ennead.cc/revenue")  

# Sidebar: data source
st.sidebar.header("Data")
default_path = "../gacha_rev_oct-jan_top_30.csv"
csv_file = st.sidebar.file_uploader("Upload CSV (optional)", type=["csv"])
path_input = st.sidebar.text_input("...or CSV path", value=default_path)

if csv_file is not None:
    df, month_cols = load_data(csv_file)
else:
    df_path = Path(path_input)
    if not df_path.exists():
        st.error(f"CSV not found: {df_path}")
        st.stop()
    df, month_cols = load_data(str(df_path))

# Sidebar filters
st.sidebar.header("Filters")

scopes = sorted([s for s in df["Scope"].dropna().unique()])
selected_scopes = st.sidebar.multiselect("Scope", scopes, default=scopes)

games = sorted(df["Game"].dropna().unique())
selected_games = st.sidebar.multiselect("Games (optional)", games, default=[])

show_only_with_month = st.sidebar.checkbox("Only games with data in selected month", value=True)
top_n = st.sidebar.slider("Top N (bar chart)", min_value=5, max_value=30, value=15, step=1)

# Reset filters (basic)
if st.sidebar.button("Reset filters"):
    st.session_state.clear()
    st.rerun()

# Apply filters
df_f = df[df["Scope"].isin(selected_scopes)] if selected_scopes else df
if selected_games:
    df_f = df_f[df_f["Game"].isin(selected_games)]

# Month selection (drives KPIs + charts)
month = st.selectbox("Month", month_cols, index=len(month_cols) - 1)
month_num = month + "_num"

if show_only_with_month:
    df_f = df_f[df_f[month_num].notna()]

# Latest month = currently selected month (keeps the dashboard consistent)
latest = month
latest_num = latest + "_num"

# ----------------------------
# KPI row
# ----------------------------
col1, col2, col3 = st.columns(3)

col1.metric("Games shown", len(df_f))

if len(df_f) and df_f[latest_num].notna().any():
    total_latest = df_f[latest_num].sum()
    col2.metric(f"Total ({latest})", f"${total_latest:,.0f}")

    top_idx = df_f[latest_num].idxmax()
    top_game = df_f.loc[top_idx, "Game"]
    col3.metric(f"Top game ({latest})", top_game)
else:
    col2.metric(f"Total ({latest})", "—")
    col3.metric(f"Top game ({latest})", "—")

# ----------------------------
# Charts row
# ----------------------------
left, right = st.columns([2, 1])

with left:
    st.subheader("Top games by selected month")

    top_df = df_f.sort_values(month_num, ascending=False).head(top_n)
    fig = px.bar(
        top_df,
        x=month_num,
        y="Game",
        orientation="h",
        color="Scope",
        labels={month_num: "Revenue (USD)"},
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending"},
        xaxis_tickprefix="$",
        xaxis_tickformat=",.0f",
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Scope split (selected month)")
    if len(df_f) and df_f[latest_num].notna().any():
        scope_sum = df_f.groupby("Scope", dropna=False)[latest_num].sum().reset_index()
        scope_sum = scope_sum.sort_values(latest_num, ascending=False)
        fig2 = px.pie(scope_sum, names="Scope", values=latest_num, hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data for current filter / month.")

st.markdown("---")

# ----------------------------
# Trends + deltas
# ----------------------------
st.subheader("Revenue trends")

num_cols = [c + "_num" for c in month_cols]
long = df_f[["Game", "Scope"] + num_cols].melt(
    id_vars=["Game", "Scope"],
    var_name="Month",
    value_name="Revenue",
)
long["Month"] = long["Month"].str.replace("_num", "", regex=False)
long["Month"] = month_order_cat(long["Month"], month_cols)

# If user didn't pick games, show top 8 by total across months
if not selected_games and len(df_f):
    totals = df_f[num_cols].sum(axis=1).sort_values(ascending=False)
    top_games = df_f.loc[totals.head(8).index, "Game"].tolist()
    long_plot = long[long["Game"].isin(top_games)]
else:
    long_plot = long

fig3 = px.line(long_plot, x="Month", y="Revenue", color="Game", markers=True)
fig3.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
st.plotly_chart(fig3, use_container_width=True)

# Month-over-month delta view (if possible)
month_idx = month_cols.index(month)
if month_idx > 0:
    prev_month = month_cols[month_idx - 1]
    prev_num = prev_month + "_num"

    st.subheader(f"Month-over-month change: {prev_month} → {month}")

    delta_df = df_f[["Game", "Scope", prev_num, month_num]].copy()
    delta_df["Delta"] = delta_df[month_num] - delta_df[prev_num]
    delta_df = delta_df.dropna(subset=["Delta"]).sort_values("Delta", ascending=False).head(top_n)

    fig4 = px.bar(delta_df, x="Delta", y="Game", orientation="h", color="Scope")
    fig4.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_tickprefix="$", xaxis_tickformat=",.0f")
    st.plotly_chart(fig4, use_container_width=True)

# ----------------------------
# Data table
# ----------------------------
st.subheader("Data table")
st.markdown(
    "Missing values indicate that the game did not make Top 30 for the respective month.\n\n"
    "**Note:** Arknights: Endfield and Dragon Traveler were only released in Jan."
)

st.dataframe(df_f[["Game", "Scope"] + month_cols], use_container_width=True)
