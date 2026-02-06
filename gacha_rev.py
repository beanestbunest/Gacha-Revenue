import re
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Gacha Revenue (Top 30)", layout="wide")

@st.cache_data
def load_data(path: str):
    df = pd.read_csv(path, na_values=["N.A.", "NA", "N/A", "-"])
    df.columns = (
        df.columns.astype(str)
        .str.replace("–", "-", regex=False)   # just in case
        .str.replace("‑", "-", regex=False)   # just in case
        .str.strip()
    )

    # If your CSV already uses Oct/Nov/Dec/Jan, this does nothing harmful.
    df = df.rename(columns={"Oct-25": "Oct", "Nov-25": "Nov", "Dec-25": "Dec", "Jan-26": "Jan"})

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

        s = re.sub(r"[^0-9.]", "", s)  # remove $ and commas

        # handle OCR/placeholder weirdness like '.', '..', '...'
        if s == "" or set(s) == {"."}:
            return None

        return float(s)

    for c in month_cols:
        df[c + "_num"] = df[c].apply(money_to_float)

    return df, month_cols

# ---- Change this path to your file location
df, month_cols = load_data("../own_data/gacha_rev_oct-jan_top_30.csv")

st.title("Gacha Revenue Dashboard (Top 30 per Month)")
st.markdown("Data taken from https://revenue.ennead.cc/revenue")

# ---- Sidebar filters
st.sidebar.header("Filters")
scopes = sorted([s for s in df["Scope"].dropna().unique()])
selected_scopes = st.sidebar.multiselect("Scope", scopes, default=scopes)

games = sorted(df["Game"].unique())
selected_games = st.sidebar.multiselect("Games (optional)", games, default=[])

df_f = df[df["Scope"].isin(selected_scopes)] if selected_scopes else df
if selected_games:
    df_f = df_f[df_f["Game"].isin(selected_games)]

latest = "Jan"

# ---- KPI row
col1, col2, col3 = st.columns(3)
col1.metric("Games shown", len(df_f))
col2.metric(f"Total ({latest})", f"${df_f[latest + '_num'].sum():,.0f}" if len(df_f) else "—")
col3.metric(
    "Top game (latest)",
    df_f.loc[df_f[latest + "_num"].idxmax(), "Game"] if len(df_f) else "—"
)

# ---- Charts
left, right = st.columns([2, 1])

with left:
    st.subheader("Top games by selected month")
    month = st.selectbox("Month", month_cols, index=len(month_cols) - 1)

    top_df = df_f.sort_values(month + "_num", ascending=False).head(15)
    fig = px.bar(top_df, x=month + "_num", y="Game", orientation="h", color="Scope")
    fig.update_layout(yaxis={"categoryorder": "total ascending"}, xaxis_title="Revenue (USD)")
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Scope split (latest month)")
    if len(df_f):
        scope_sum = df_f.groupby("Scope", dropna=False)[latest + "_num"].sum().reset_index()
        fig2 = px.pie(scope_sum, names="Scope", values=latest + "_num", hole=0.4)
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data for current filter.")

st.markdown("---")
st.subheader("Revenue trends")

# Reshape to long for line chart
num_cols = [c + "_num" for c in month_cols]
long = df_f[["Game", "Scope"] + num_cols].melt(
    id_vars=["Game", "Scope"],
    var_name="Month",
    value_name="Revenue"
)
long["Month"] = long["Month"].str.replace("_num", "", regex=False)

# If user didn't pick games, show top 8 by total across months
if not selected_games and len(df_f):
    totals = df_f[num_cols].sum(axis=1).sort_values(ascending=False)
    top_games = df_f.loc[totals.head(8).index, "Game"].tolist()
    long = long[long["Game"].isin(top_games)]

fig3 = px.line(long, x="Month", y="Revenue", color="Game", markers=True)
st.plotly_chart(fig3, use_container_width=True)

st.subheader("Data table")
st.markdown(
    "### Missing values indicate that the game did not make Top 30 for the repsective month\n"
    "**Note:** Arknights: Endfield and Dragon Traveler were only released in Jan."
)
st.dataframe(df_f[["Game", "Scope"] + month_cols], use_container_width=True)
