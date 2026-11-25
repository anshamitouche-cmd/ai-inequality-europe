import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

# ==============================================================================
# PAGE CONFIGURATION & EDITORIAL STYLING
# ==============================================================================
st.set_page_config(
    page_title="AI: Engine of Growth or Driver of Inequality?",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .stApp { background-color: #F8FAFC; }
    .block-container { padding-top: 1.6rem; padding-bottom: 3rem; max-width: 1500px; }
    footer, #MainMenu { visibility: hidden; }

    /* Hero */
    .hero-box {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 62%, #2563EB 100%);
        padding: 1.9rem 2.3rem; border-radius: 16px; color: white;
        margin-bottom: 1.4rem; box-shadow: 0 12px 28px -8px rgba(15,23,42,.35);
    }
    .hero-kicker { font-size:.78rem; letter-spacing:.14em; text-transform:uppercase; color:#93C5FD; font-weight:700; margin-bottom:.5rem; }
    .hero-title { font-size:2rem; font-weight:800; line-height:1.2; margin-bottom:.5rem; letter-spacing:-0.02em; }
    .hero-subtitle { font-size:1.02rem; color:#DBEAFE; margin:0; }

    /* KPI cards */
    .kpi-card {
        background:white; padding:1.1rem 1.3rem; border-radius:14px;
        border-left:5px solid #2563EB; box-shadow:0 4px 14px rgba(15,23,42,.06);
        margin-bottom:1rem; transition: transform .15s ease, box-shadow .15s ease; height: 100%;
    }
    .kpi-card:hover { transform: translateY(-3px); box-shadow:0 10px 22px rgba(15,23,42,.12); }
    .kpi-card.emerald { border-left-color:#10B981; }
    .kpi-card.amber   { border-left-color:#F59E0B; }
    .kpi-card.crimson { border-left-color:#EF4444; }
    .kpi-label { font-size:.76rem; text-transform:uppercase; letter-spacing:.06em; color:#64748B; font-weight:700; }
    .kpi-value { font-size:1.9rem; font-weight:800; color:#0F172A; margin:.15rem 0; }
    .kpi-delta { font-size:.84rem; color:#475569; }

    /* Storytelling box */
    .story-box {
        background:#EFF6FF; border-left:4px solid #2563EB; padding:1rem 1.3rem;
        border-radius:0 12px 12px 0; margin:.6rem 0 1.2rem 0; color:#1E293B; font-size:.96rem;
    }
    .story-box strong { color:#1D4ED8; }
    .caveat {
        background:#FFFBEB; border-left:4px solid #F59E0B; padding:.7rem 1rem;
        border-radius:0 10px 10px 0; color:#78350F; font-size:.86rem; margin:.4rem 0 1rem 0;
    }
    .chart-note { color:#64748B; font-size:.82rem; margin:-.3rem 0 1.2rem 0; }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] { gap:6px; border-bottom:1px solid #E2E8F0; flex-wrap: wrap; }
    .stTabs [data-baseweb="tab"] {
        background:white; border-radius:10px 10px 0 0; padding:.55rem 1rem;
        border:1px solid #E2E8F0; border-bottom:none; font-weight:600;
    }
    .stTabs [aria-selected="true"] { background:#1E3A8A !important; color:white !important; }
    .stTabs [aria-selected="true"] p { color:white !important; }

    /* Section headers */
    h3 { color:#0F172A; letter-spacing:-0.01em; }
</style>
""",
    unsafe_allow_html=True,
)

# ==============================================================================
# CONSTANTS
# ==============================================================================
COUNTRY_COLORS = {
    "France": "#2563EB",
    "Germany": "#10B981",
    "Spain": "#F59E0B",
    "Italy": "#EF4444",
    "EU-27 Average": "#8B5CF6",
}
COUNTRY_NAMES = {"FR": "France", "DE": "Germany", "ES": "Spain", "IT": "Italy", "EU27_2020": "EU-27 Average"}
TARGET_GEOS = list(COUNTRY_NAMES.keys())
TARGET_YEARS = [2021, 2022, 2023, 2024, 2025]
FONT = "Inter, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
STANFORD_INVEST_BN = 581.7  # Stanford AI Index 2026, corporate AI investment 2025 (US$ bn)

PLOT_CONFIG = {
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2},
}

VAR_LABELS = {
    "ai_total": "AI adoption – all firms 10+ (%)",
    "ai_small": "AI adoption – small firms 10–49 (%)",
    "ai_medium": "AI adoption – medium firms 50–249 (%)",
    "ai_large": "AI adoption – large firms 250+ (%)",
    "ai_gap_large_small": "Large–small adoption gap (pp)",
    "prod_hourly_growth": "Hourly productivity growth (%)",
    "prod_hourly_idx": "Hourly productivity index (2015=100)",
    "ulc_hourly_growth": "Unit labour cost growth (%)",
    "ulc_hourly_idx": "Unit labour cost index (2015=100)",
    "ai_job_postings_pct": "AI job postings (% of postings)",
    "job_vacancy_rate": "Job vacancy rate (%)",
    "poverty_arop": "At-risk-of-poverty rate (%)",
    "mfg_emp_share": "Manufacturing share of employment (%)",
}
CORR_COLS = [
    "ai_total", "ai_gap_large_small", "prod_hourly_growth", "ulc_hourly_growth",
    "ai_job_postings_pct", "job_vacancy_rate", "poverty_arop", "mfg_emp_share",
]

ST_VERSION = tuple(int(x) for x in re.findall(r"\d+", st.__version__)[:2])
NEW_WIDTH_API = ST_VERSION >= (1, 49)


# ==============================================================================
# SMALL HELPERS
# ==============================================================================
def show(fig, key):
    """Render a Plotly figure full width (compatible with old & new Streamlit)."""
    if NEW_WIDTH_API:
        st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG, key=key)
    else:
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG, key=key)


def show_df(df, **kwargs):
    if NEW_WIDTH_API:
        st.dataframe(df, width="stretch", **kwargs)
    else:
        st.dataframe(df, use_container_width=True, **kwargs)


def style(fig, height=450, title=None, legend_bottom=False, top=70):
    fig.update_layout(
        template="plotly_white",
        font=dict(family=FONT, size=13, color="#1E293B"),
        height=height,
        paper_bgcolor="white",
        plot_bgcolor="white",
        margin=dict(l=20, r=25, t=top, b=20),
        title=dict(text=title, x=0.01, xanchor="left", font=dict(size=16, color="#0F172A")) if title else None,
        hoverlabel=dict(bgcolor="white", font_size=13, bordercolor="#CBD5E1"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5, title_text="")
        if legend_bottom
        else dict(title_text=""),
    )
    fig.update_xaxes(showline=True, linecolor="#CBD5E1", gridcolor="#EEF2F7", zeroline=False)
    fig.update_yaxes(showline=False, gridcolor="#EEF2F7", zeroline=False)
    return fig


def fmt(x, nd=1, suffix="", plus=False):
    if x is None or pd.isna(x):
        return "n/a"
    sign = "+" if plus and x > 0 else ""
    return f"{sign}{x:.{nd}f}{suffix}"


def kpi(label, value, delta, cls=""):
    st.markdown(
        f"""<div class="kpi-card {cls}"><div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div><div class="kpi-delta">{delta}</div></div>""",
        unsafe_allow_html=True,
    )


def corr_stats(x: pd.Series, y: pd.Series):
    d = pd.concat([x, y], axis=1).dropna()
    n = len(d)
    if n < 4 or d.iloc[:, 0].std() == 0 or d.iloc[:, 1].std() == 0:
        return np.nan, np.nan, n
    return d.corr().iloc[0, 1], d.corr(method="spearman").iloc[0, 1], n


def strength(r):
    if r is None or pd.isna(r):
        return "undetermined"
    a = abs(r)
    word = "very weak" if a < 0.2 else "weak" if a < 0.4 else "moderate" if a < 0.6 else "strong"
    return f"{word} {'positive' if r > 0 else 'negative'}"


def spread_labels(vals, gap):
    """Nudge label positions so that they never overlap (slopegraph)."""
    vals = np.asarray(vals, dtype=float)
    order = np.argsort(vals)
    pos = vals[order].copy()
    adj = pos.copy()
    for i in range(1, len(adj)):
        if adj[i] - adj[i - 1] < gap:
            adj[i] = adj[i - 1] + gap
    adj += pos.mean() - adj.mean()
    out = np.empty_like(adj)
    out[order] = adj
    return out


def find_csv(stem: str) -> Path:
    base = Path(__file__).parent
    cands = []
    for folder in (base / "data", base):
        for sep in ("$", "_"):
            cands.append(folder / f"{stem}{sep}defaultview_linear.csv")
        cands.append(folder / f"{stem}.csv")
    for c in cands:
        if c.exists():
            return c
    raise FileNotFoundError(f"Could not find the dataset '{stem}' in ./data/ (tried {[str(c.name) for c in cands[:3]]}).")


def standardize_geo(series):
    mapping = {
        "France": "FR",
        "Germany": "DE", "Allemagne": "DE",
        "Spain": "ES", "Espagne": "ES",
        "Italy": "IT", "Italie": "IT",
        "European Union - 27 countries (from 2020)": "EU27_2020",
        "Union européenne - 27 pays (à partir de 2020)": "EU27_2020",
    }
    return series.map(mapping)


# ==============================================================================
# DATA LOADING & CLEANING PIPELINE (CACHED)
# ==============================================================================
@st.cache_data(show_spinner="Loading Eurostat & OWID datasets…")
def load_all_data():
    # 1. AI adoption by firm size (isoc_eb_ai) ---------------------------------
    raw = pd.read_csv(find_csv("isoc_eb_ai"))
    raw["geo"] = standardize_geo(raw["geo"])
    df_ai = (
        raw[
            raw["geo"].isin(TARGET_GEOS)
            & raw["TIME_PERIOD"].isin(TARGET_YEARS)
            & raw["indic_is"].str.startswith("Enterprises using at least one of the AI technologies")
        ]
        .pivot_table(index=["geo", "TIME_PERIOD"], columns="size_emp", values="OBS_VALUE")
        .reset_index()
        .rename(columns={
            "TIME_PERIOD": "year",
            "10 persons employed or more": "ai_total",
            "From 10 to 49 persons employed": "ai_small",
            "From 50 to 249 persons employed": "ai_medium",
            "250 persons employed or more": "ai_large",
        })
    )
    df_ai["ai_gap_large_small"] = df_ai["ai_large"] - df_ai["ai_small"]

    # 2. AI adoption by sector (isoc_eb_ain2) ----------------------------------
    raw = pd.read_csv(find_csv("isoc_eb_ain2"))
    raw["geo"] = standardize_geo(raw["geo"])
    df_sec = raw[
        raw["geo"].isin(TARGET_GEOS)
        & raw["TIME_PERIOD"].isin(TARGET_YEARS)
        & raw["indic_is"].str.startswith("Enterprises using at least one of the AI technologies")
        & ~raw["nace_r2"].str.startswith("All activities")
    ].copy()
    sector_map = {
        "Information and communication": "ICT & Media",
        "Professional, scientific and technical activities": "Scientific & Tech",
        "Administrative and support service activities": "Admin & Support",
        "Electricity, gas, steam and air conditioning supply": "Energy Supply",
        "Manufacturing": "Manufacturing",
        "Wholesale and retail trade; repair of motor vehicles and motorcycles": "Wholesale & Retail",
        "Transportation and storage": "Transport & Storage",
        "Real estate activities": "Real Estate",
        "Water supply; sewerage, waste management and remediation activities": "Water & Waste",
        "Accommodation and food service activities": "Hospitality",
        "Construction": "Construction",
    }
    df_sec["sector"] = df_sec["nace_r2"].map(sector_map).fillna(df_sec["nace_r2"])
    df_sec["country_name"] = df_sec["geo"].map(COUNTRY_NAMES)
    df_sec = df_sec[["geo", "country_name", "TIME_PERIOD", "sector", "OBS_VALUE"]].rename(
        columns={"TIME_PERIOD": "year", "OBS_VALUE": "ai_adoption"}
    )

    # 3. Productivity & unit labour costs (nama_10_lp_ulc) – full 2016-2025 -----
    raw = pd.read_csv(find_csv("nama_10_lp_ulc"))
    raw["geo"] = standardize_geo(raw["geo"])
    sub = raw[raw["geo"].isin(TARGET_GEOS)].copy()
    prod = sub["na_item"] == "Real labour productivity per hour worked"
    ulc = sub["na_item"] == "Nominal unit labour cost based on hours worked"
    idx = sub["unit"] == "Index, 2015=100"
    gr = sub["unit"] == "Percentage change on previous period"
    sub["metric"] = np.select(
        [prod & idx, prod & gr, ulc & idx, ulc & gr],
        ["prod_hourly_idx", "prod_hourly_growth", "ulc_hourly_idx", "ulc_hourly_growth"],
        default="other",
    )
    df_ulc_long = (
        sub[sub["metric"] != "other"]
        .pivot_table(index=["geo", "TIME_PERIOD"], columns="metric", values="OBS_VALUE")
        .reset_index()
        .rename(columns={"TIME_PERIOD": "year"})
    )
    df_ulc_long["country_name"] = df_ulc_long["geo"].map(COUNTRY_NAMES)

    # 4. Employment & manufacturing share (lfsa_egan2) -------------------------
    raw = pd.read_csv(find_csv("lfsa_egan2"))
    raw["geo"] = standardize_geo(raw["geo"])
    df_emp = (
        raw[
            raw["geo"].isin(TARGET_GEOS)
            & raw["TIME_PERIOD"].isin(TARGET_YEARS)
            & (raw["sex"] == "Total")
            & raw["nace_r2"].isin(["Total - all NACE activities", "Manufacturing"])
        ]
        .pivot_table(index=["geo", "TIME_PERIOD"], columns="nace_r2", values="OBS_VALUE")
        .reset_index()
        .rename(columns={"TIME_PERIOD": "year"})
    )
    df_emp["mfg_emp_share"] = df_emp["Manufacturing"] / df_emp["Total - all NACE activities"] * 100

    # 5. Job vacancy rate (jvs_q_r21) – quarterly -> annual --------------------
    raw = pd.read_csv(find_csv("jvs_q_r21"))
    raw["geo"] = standardize_geo(raw["geo"])
    sub = raw[
        raw["geo"].isin(TARGET_GEOS)
        & raw["TIME_PERIOD"].str.match(r"^202[1-5]")
        & (raw["indic_em"] == "Taux de vacances d'emplois")
        & (raw["sizeclas"] == "10 salariés ou plus")
        & raw["s_adj"].str.startswith("Données non ajustées")
    ].copy()
    sub["year"] = sub["TIME_PERIOD"].str[:4].astype(int)
    sub["group"] = np.select(
        [
            sub["nace_r2_1"] == "Industrie et services marchands",
            sub["nace_r2_1"] == "Industrie et construction",
            sub["nace_r2_1"].str.startswith("Industrie, construction et services"),
        ],
        ["Industry & market services", "Industry & construction", "Whole economy"],
        default="other",
    )
    sub = sub[sub["group"] != "other"]
    df_jvs_sec = sub.groupby(["geo", "year", "group"], as_index=False)["OBS_VALUE"].mean().rename(
        columns={"OBS_VALUE": "job_vacancy_rate"}
    )
    df_jvs_sec["country_name"] = df_jvs_sec["geo"].map(COUNTRY_NAMES)
    df_jvs = (
        df_jvs_sec[df_jvs_sec["group"] == "Industry & market services"][["geo", "year", "job_vacancy_rate"]]
        .reset_index(drop=True)
    )

    # 6. At-risk-of-poverty (ilc_li02) – full 2016-2025 ------------------------
    raw = pd.read_csv(find_csv("ilc_li02"))
    raw["geo"] = standardize_geo(raw["geo"])
    df_pov_long = raw[
        raw["geo"].isin(TARGET_GEOS)
        & (raw["statinfo"] == "Revenu équivalent médian")
        & (raw["unit"] == "Pourcentage")
        & (raw["sex"] == "Total")
        & (raw["age"] == "Total")
    ][["geo", "TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "year", "OBS_VALUE": "poverty_arop"})
    df_pov_long["country_name"] = df_pov_long["geo"].map(COUNTRY_NAMES)

    # 7. AI job postings (OWID / Lightcast) ------------------------------------
    raw = pd.read_csv(find_csv("share-artificial-intelligence-job-postings"))
    raw["geo"] = raw["Code"].map({"FRA": "FR", "DEU": "DE", "ESP": "ES", "ITA": "IT"})
    df_owid = raw[raw["geo"].isin(TARGET_GEOS)].copy()
    df_owid["country_name"] = df_owid["geo"].map(COUNTRY_NAMES)
    df_owid = df_owid.rename(columns={
        "Year": "year",
        "Share of artificial intelligence jobs among all job postings": "ai_job_postings_pct",
    })[["geo", "country_name", "year", "ai_job_postings_pct"]]

    # Master panel -------------------------------------------------------------
    grid = pd.MultiIndex.from_product([TARGET_GEOS, TARGET_YEARS], names=["geo", "year"]).to_frame(index=False)
    ulc_cols = ["geo", "year", "prod_hourly_idx", "prod_hourly_growth", "ulc_hourly_idx", "ulc_hourly_growth"]
    master = (
        grid
        .merge(df_ai, on=["geo", "year"], how="left")
        .merge(df_ulc_long[ulc_cols], on=["geo", "year"], how="left")
        .merge(df_emp[["geo", "year", "mfg_emp_share"]], on=["geo", "year"], how="left")
        .merge(df_jvs, on=["geo", "year"], how="left")
        .merge(df_pov_long[["geo", "year", "poverty_arop"]], on=["geo", "year"], how="left")
        .merge(df_owid[["geo", "year", "ai_job_postings_pct"]], on=["geo", "year"], how="left")
    )
    master["country_name"] = master["geo"].map(COUNTRY_NAMES)
    master["ai_talent_tension"] = master["ai_job_postings_pct"] / master["ai_total"]
    first_pov = master.groupby("geo")["poverty_arop"].transform("first")
    master["poverty_change_since_2021"] = master["poverty_arop"] - first_pov
    return master, df_sec, df_owid, df_ulc_long, df_pov_long, df_jvs_sec


try:
    df_master, df_sec, df_owid_hist, df_ulc_long, df_pov_long, df_jvs_sec = load_all_data()
except FileNotFoundError as err:
    st.error(f"**Data file missing.** {err}\n\nPut the 7 CSV files in a `data/` folder next to `app.py`.")
    st.stop()

AI_YEARS = sorted(df_master.dropna(subset=["ai_total"])["year"].unique().tolist())
LATEST_AI_YEAR = max(AI_YEARS)
FIRST_AI_YEAR = min(AI_YEARS)
ALL_COUNTRIES = list(COUNTRY_COLORS.keys())

# ==============================================================================
# SIDEBAR
# ==============================================================================
st.session_state.setdefault("countries", ALL_COUNTRIES)
st.session_state.setdefault("focus_year", LATEST_AI_YEAR)
st.session_state.setdefault("show_notes", True)


def reset_filters():
    st.session_state["countries"] = ALL_COUNTRIES
    st.session_state["focus_year"] = LATEST_AI_YEAR
    st.session_state["show_notes"] = True


with st.sidebar:
    st.markdown("## 🎛️ Dashboard controls")
    selected_countries = st.multiselect("Economies to compare", options=ALL_COUNTRIES, key="countries")
    focus_year = st.select_slider(
        "Snapshot year (firm size & sectors)", options=AI_YEARS, key="focus_year",
        help="Eurostat's AI survey covers 2021, 2023, 2024 and 2025 (no 2022 wave).",
    )
    show_notes = st.toggle("Show narrative boxes", key="show_notes")
    st.button("↺ Reset filters", on_click=reset_filters, use_container_width=True)
    st.markdown("---")
    st.markdown("**💡 How to explore**")
    st.caption(
        "Hover for exact values · click a legend entry to hide it, double-click to isolate it · "
        "drag to zoom, double-click to reset · camera icon = PNG export."
    )
    st.markdown("---")
    st.caption(
        "**Sources:** Eurostat (`isoc_eb_ai`, `isoc_eb_ain2`, `nama_10_lp_ulc`, `lfsa_egan2`, `jvs_q_r21`, "
        "`ilc_li02`), Lightcast via Our World in Data, Stanford AI Index 2026."
    )

if not selected_countries:
    st.warning("Select at least one economy in the sidebar to display the charts.")
    st.stop()

df_m_filt = df_master[df_master["country_name"].isin(selected_countries)]
df_s_filt = df_sec[df_sec["country_name"].isin(selected_countries)]
df_o_filt = df_owid_hist[df_owid_hist["country_name"].isin(selected_countries)]
df_u_filt = df_ulc_long[df_ulc_long["country_name"].isin(selected_countries)]
df_p_filt = df_pov_long[df_pov_long["country_name"].isin(selected_countries)]
countries_only = [c for c in selected_countries if c != "EU-27 Average"]

# ==============================================================================
# HERO & KPI CARDS
# ==============================================================================
st.markdown(
    """
<div class="hero-box">
    <div class="hero-kicker">Data story · Europe · 2021–2025</div>
    <div class="hero-title">Is Artificial Intelligence a Driver of Economic Development, or a Catalyst for Inequality?</div>
    <p class="hero-subtitle">Capital flows, firm-level diffusion, productivity, labour-market tension and poverty risk in France, Germany, Spain, Italy and the EU-27</p>
</div>
""",
    unsafe_allow_html=True,
)

eu = df_master[df_master["geo"] == "EU27_2020"].set_index("year")


def eu_val(col, year):
    try:
        return eu.loc[year, col]
    except KeyError:
        return np.nan


ai_now, ai_base = eu_val("ai_total", focus_year), eu_val("ai_total", FIRST_AI_YEAR)
gap_now, gap_base = eu_val("ai_gap_large_small", focus_year), eu_val("ai_gap_large_small", FIRST_AI_YEAR)
pov_now, pov_base = eu_val("poverty_arop", focus_year), eu_val("poverty_arop", FIRST_AI_YEAR)

k1, k2, k3, k4 = st.columns(4)
with k1:
    kpi("Global corporate AI investment", f"${STANFORD_INVEST_BN:,.1f}B",
        "2025 · Stanford AI Index 2026 (corporate investment)")
with k2:
    kpi(f"EU-27 AI adoption ({focus_year})", fmt(ai_now, 1, "%"),
        f"{fmt(ai_now - ai_base, 1, ' pp', plus=True)} vs. {FIRST_AI_YEAR} · firms with 10+ employees", "emerald")
with k3:
    kpi("Large vs. small firm gap", fmt(gap_now, 1, " pp", plus=True),
        f"250+ vs. 10–49 employees · {fmt(gap_now - gap_base, 1, ' pp', plus=True)} vs. {FIRST_AI_YEAR}", "amber")
with k4:
    kpi("EU-27 poverty risk (AROP)", fmt(pov_now, 1, "%"),
        f"{fmt(pov_now - pov_base, 1, ' pp', plus=True)} vs. {FIRST_AI_YEAR} · below 60% of median income", "crimson")

# ==============================================================================
# TABS
# ==============================================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🌍 Act I · Market surge & diffusion",
    "⚙️ Act II · Productivity & firm divide",
    "⚖️ Act III · Labour market & inequality",
    "🧭 Synthesis & explorer",
])

# ------------------------------------------------------------------------------
# TAB 1
# ------------------------------------------------------------------------------
with tab1:
    if show_notes:
        st.markdown(
            f"""<div class="story-box"><strong>Act I · The hook.</strong> Global corporate AI investment reached
            <strong>${STANFORD_INVEST_BN:,.1f}B</strong> in 2025. But how fast is AI actually reaching European firms —
            and <em>which</em> firms and sectors? Adoption in the EU-27 went from <strong>{fmt(ai_base,1,'%')}</strong>
            ({FIRST_AI_YEAR}) to <strong>{fmt(eu_val('ai_total', LATEST_AI_YEAR),1,'%')}</strong> ({LATEST_AI_YEAR}).</div>""",
            unsafe_allow_html=True,
        )

    left, right = st.columns([1.1, 1])

    # 1.1 Slopegraph with selectable years
    with left:
        if len(AI_YEARS) > 1:
            yr_a, yr_b = st.select_slider(
                "Compare two survey years", options=AI_YEARS, value=(FIRST_AI_YEAR, focus_year), key="slope_years"
            )
        else:
            yr_a = yr_b = AI_YEARS[0]
        df_sl = df_m_filt[df_m_filt["year"].isin([yr_a, yr_b])].dropna(subset=["ai_total"])
        names = [c for c in selected_countries if (df_sl["country_name"] == c).sum() == 2]
        if yr_a == yr_b or not names:
            st.info("Pick two different years to see the slopegraph.")
        else:
            fig = go.Figure()
            va = [df_sl[(df_sl.country_name == c) & (df_sl.year == yr_a)]["ai_total"].iloc[0] for c in names]
            vb = [df_sl[(df_sl.country_name == c) & (df_sl.year == yr_b)]["ai_total"].iloc[0] for c in names]
            rng = max(max(va + vb) - min(va + vb), 1)
            la, lb = spread_labels(va, rng * 0.065), spread_labels(vb, rng * 0.065)
            ann = []
            for i, c in enumerate(names):
                col = COUNTRY_COLORS[c]
                fig.add_trace(go.Scatter(
                    x=[str(yr_a), str(yr_b)], y=[va[i], vb[i]], mode="lines+markers", name=c,
                    line=dict(color=col, width=4), marker=dict(size=11, line=dict(color="white", width=2)),
                    hovertemplate=f"<b>{c}</b><br>%{{x}}: %{{y:.1f}}%<extra></extra>",
                ))
                ann.append(dict(x=str(yr_a), y=la[i], text=f"{va[i]:.1f}%", showarrow=False, xanchor="right",
                                xshift=-14, font=dict(color=col, size=12)))
                ann.append(dict(x=str(yr_b), y=lb[i], text=f"<b>{c}</b> {vb[i]:.1f}% ({vb[i]-va[i]:+.1f} pp)",
                                showarrow=False, xanchor="left", xshift=14, font=dict(color=col, size=12)))
            fig.update_layout(annotations=ann, showlegend=False)
            fig.update_xaxes(type="category", range=[-0.55, 2.0], showgrid=False, title="")
            fig.update_yaxes(title="Enterprise AI adoption (%)", ticksuffix="%")
            style(fig, 470, f"1.1 The post-generative-AI leap ({yr_a} → {yr_b})")
            show(fig, "slope")

    # 1.2 Sector view: bars or treemap
    with right:
        c1, c2 = st.columns([1.2, 1])
        with c1:
            sec_options = selected_countries
            default_idx = sec_options.index("EU-27 Average") if "EU-27 Average" in sec_options else 0
            sec_country = st.selectbox("Zone", sec_options, index=default_idx, key="sec_country")
        with c2:
            sec_view = st.radio("View", ["Ranked bars", "Treemap"], horizontal=True, key="sec_view")
        d = df_sec[(df_sec["country_name"] == sec_country) & (df_sec["year"] == focus_year)].dropna(subset=["ai_adoption"])
        if d.empty:
            st.info("No sector data for this selection.")
        elif sec_view == "Treemap":
            fig = px.treemap(
                d, path=[px.Constant(f"{sec_country} · {focus_year}"), "sector"], values="ai_adoption",
                color="ai_adoption", color_continuous_scale="Blues",
            )
            fig.update_traces(
                texttemplate="<b>%{label}</b><br>%{value:.1f}%",
                hovertemplate="<b>%{label}</b><br>AI adoption: %{value:.1f}%<extra></extra>",
            )
            fig.update_layout(coloraxis_showscale=False)
            style(fig, 470, f"1.2 Sector concentration of AI — {sec_country} ({focus_year})")
            show(fig, "tree")
        else:
            d = d.sort_values("ai_adoption")
            fig = go.Figure(go.Bar(
                x=d["ai_adoption"], y=d["sector"], orientation="h",
                marker=dict(color=d["ai_adoption"], colorscale="Blues", cmin=0, cmax=max(d["ai_adoption"].max(), 1) * 1.1),
                text=[f"{v:.1f}%" for v in d["ai_adoption"]], textposition="outside", cliponaxis=False,
                hovertemplate="<b>%{y}</b><br>AI adoption: %{x:.1f}%<extra></extra>", name=sec_country,
            ))
            if sec_country != "EU-27 Average":
                e = df_sec[(df_sec["geo"] == "EU27_2020") & (df_sec["year"] == focus_year)].set_index("sector")["ai_adoption"]
                fig.add_trace(go.Scatter(
                    x=[e.get(s, np.nan) for s in d["sector"]], y=d["sector"], mode="markers", name="EU-27 average",
                    marker=dict(symbol="diamond", size=11, color="#8B5CF6", line=dict(color="white", width=1.5)),
                    hovertemplate="<b>%{y}</b><br>EU-27: %{x:.1f}%<extra></extra>",
                ))
            fig.update_xaxes(ticksuffix="%", range=[0, d["ai_adoption"].max() * 1.2])
            style(fig, 470, f"1.2 AI adoption by sector — {sec_country} ({focus_year})", legend_bottom=True)
            show(fig, "sector_bars")

    # 1.3 Time evolution by firm size
    size_map = {
        "All firms (10+ employees)": "ai_total",
        "Small (10–49)": "ai_small",
        "Medium (50–249)": "ai_medium",
        "Large (250+)": "ai_large",
    }
    size_label = st.radio("Firm size", list(size_map.keys()), horizontal=True, key="size_radio")
    scol = size_map[size_label]
    fig = go.Figure()
    for c in selected_countries:
        s = df_m_filt[df_m_filt["country_name"] == c].dropna(subset=[scol]).sort_values("year")
        fig.add_trace(go.Scatter(
            x=s["year"], y=s[scol], mode="lines+markers", name=c,
            line=dict(color=COUNTRY_COLORS[c], width=3.5, dash="dash" if c == "EU-27 Average" else "solid"),
            marker=dict(size=9, line=dict(color="white", width=1.5)),
            hovertemplate="%{y:.1f}%",
        ))
    fig.add_vline(x=2022, line_dash="dot", line_color="#94A3B8",
                  annotation_text="no survey wave in 2022", annotation_position="top")
    fig.update_xaxes(tickmode="array", tickvals=TARGET_YEARS, title="")
    fig.update_yaxes(ticksuffix="%", title="Share of enterprises using AI", rangemode="tozero")
    fig.update_layout(hovermode="x unified")
    style(fig, 430, f"1.3 AI adoption over time — {size_label}", legend_bottom=True)
    show(fig, "evolution")
    st.markdown(
        '<div class="caveat">⚠️ <strong>Comparability.</strong> Dips between 2021 and 2023 in some countries (e.g. France, Italy) '
        'and the very sharp jump in 2024–2025 may partly reflect changes in the survey definition/coverage of AI technologies, '
        'not only real adoption. Read levels across waves with caution.</div>',
        unsafe_allow_html=True,
    )

    # 1.4 Heatmap
    df_heat = df_s_filt[df_s_filt["year"] == focus_year].pivot(index="sector", columns="country_name", values="ai_adoption")
    if not df_heat.empty:
        df_heat = df_heat.reindex(columns=[c for c in ALL_COUNTRIES if c in df_heat.columns])
        df_heat = df_heat.loc[df_heat.mean(axis=1).sort_values().index]
        fig = px.imshow(df_heat, text_auto=".1f", aspect="auto", color_continuous_scale="YlGnBu",
                        labels=dict(x="", y="", color="Adoption (%)"))
        fig.update_traces(hovertemplate="<b>%{y}</b> · %{x}<br>AI adoption: %{z:.1f}%<extra></extra>")
        style(fig, 470, f"1.4 Cross-country & cross-sector AI diffusion matrix ({focus_year}, % of firms)")
        show(fig, "heatmap")
        st.markdown('<div class="chart-note">Blank cells: Eurostat does not publish the value (confidentiality / reliability).</div>',
                    unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2
# ------------------------------------------------------------------------------
with tab2:
    if show_notes:
        prod_now = eu_val("prod_hourly_idx", LATEST_AI_YEAR)
        prod_base = eu_val("prod_hourly_idx", FIRST_AI_YEAR)
        ai_last_eu = eu_val("ai_total", LATEST_AI_YEAR)
        mult = ai_last_eu / ai_base if pd.notna(ai_base) and ai_base else np.nan
        prod_chg = (prod_now / prod_base - 1) * 100 if pd.notna(prod_base) and prod_base else np.nan
        st.markdown(
            f"""<div class="story-box"><strong>Act II · The test.</strong> Does adoption show up in the macro numbers?
            Between {FIRST_AI_YEAR} and {LATEST_AI_YEAR}, EU-27 AI adoption was multiplied by <strong>{fmt(mult,1)}×</strong>,
            while real hourly productivity moved by only <strong>{fmt(prod_chg,1,'%',plus=True)}</strong>
            (index {fmt(prod_base,1)} → {fmt(prod_now,1)}, 2015=100) — a <em>Solow-paradox</em>-type pattern: diffusion is
            fast, measurable macro gains are slow. Meanwhile, large firms pull away from small ones.</div>""",
            unsafe_allow_html=True,
        )

    # 2.1 Productivity vs ULC
    ctrl1, ctrl2 = st.columns([1, 1.4])
    with ctrl1:
        view = st.radio("Measure", ["Index (2015 = 100)", "Annual change (%)"], horizontal=True, key="prod_view")
    with ctrl2:
        yr_rng = st.slider("Years displayed", 2016, 2025, (2019, 2025), key="prod_years")
    use_idx = view.startswith("Index")
    pcol, ucol = ("prod_hourly_idx", "ulc_hourly_idx") if use_idx else ("prod_hourly_growth", "ulc_hourly_growth")
    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.08,
                        subplot_titles=("Real labour productivity per hour", "Nominal unit labour cost (hours-based)"))
    for c in selected_countries:
        s = df_u_filt[(df_u_filt["country_name"] == c) & df_u_filt["year"].between(*yr_rng)].sort_values("year")
        kw = dict(mode="lines+markers", line=dict(color=COUNTRY_COLORS[c], width=3, dash="dash" if c == "EU-27 Average" else "solid"),
                  marker=dict(size=7), legendgroup=c)
        fig.add_trace(go.Scatter(x=s["year"], y=s[pcol], name=c, hovertemplate=f"<b>{c}</b> %{{x}}: %{{y:.1f}}<extra></extra>", **kw), 1, 1)
        fig.add_trace(go.Scatter(x=s["year"], y=s[ucol], name=c, showlegend=False,
                                 hovertemplate=f"<b>{c}</b> %{{x}}: %{{y:.1f}}<extra></extra>", **kw), 1, 2)
    ref = 100 if use_idx else 0
    fig.add_hline(y=ref, line_dash="dot", line_color="#94A3B8", row="all", col="all")
    if yr_rng[1] >= 2023:
        fig.add_vrect(x0=max(2022.5, yr_rng[0] - 0.5), x1=yr_rng[1] + 0.5, fillcolor="#DBEAFE", opacity=0.35,
                      line_width=0, row="all", col="all",
                      annotation_text="gen-AI era", annotation_position="top left", annotation_font_size=11)
    fig.update_xaxes(dtick=1, title="")
    style(fig, 440, "2.1 Does AI-era growth translate into productivity or cost relief?", legend_bottom=True, top=90)
    show(fig, "prod_ulc")

    left, right = st.columns([1.15, 1])

    # 2.2 Scatter: AI adoption vs outcome
    with left:
        a, b = st.columns(2)
        with a:
            x_key = st.selectbox("AI adoption measure (X)", ["ai_total", "ai_small", "ai_large"],
                                 format_func=VAR_LABELS.get, key="sc_x")
        with b:
            y_key = st.selectbox("Outcome (Y)", ["prod_hourly_growth", "prod_hourly_idx", "ulc_hourly_growth"],
                                 format_func=VAR_LABELS.get, key="sc_y")
        trend = st.checkbox("Show OLS trend line (pooled)", value=True, key="sc_trend")
        d = df_m_filt[df_m_filt["geo"] != "EU27_2020"].dropna(subset=[x_key, y_key]).copy()
        if len(d) < 3:
            st.info("Not enough points for this selection (select more countries).")
        else:
            d["size_var"] = d["mfg_emp_share"].fillna(d["mfg_emp_share"].median())
            d["lbl"] = d["geo"] + " '" + d["year"].astype(str).str[2:]
            fig = px.scatter(
                d, x=x_key, y=y_key, size="size_var", color="country_name", text="lbl",
                color_discrete_map=COUNTRY_COLORS, size_max=30,
                labels={x_key: VAR_LABELS[x_key], y_key: VAR_LABELS[y_key], "country_name": "Country",
                        "size_var": "Manufacturing share (%)"},
                hover_data={"lbl": False, "year": True, "size_var": ":.1f"},
            )
            fig.update_traces(textposition="top center", marker=dict(opacity=0.85, line=dict(width=1.5, color="white")))
            r, rho, n = corr_stats(d[x_key], d[y_key])
            if trend and d[x_key].nunique() > 1:
                m, b0 = np.polyfit(d[x_key], d[y_key], 1)
                xs = np.linspace(d[x_key].min(), d[x_key].max(), 20)
                fig.add_trace(go.Scatter(x=xs, y=m * xs + b0, mode="lines", name="OLS trend",
                                         line=dict(color="#475569", dash="dash", width=2), hoverinfo="skip"))
            fig.update_xaxes(ticksuffix="%")
            style(fig, 470, f"2.2 AI adoption vs. outcome · r = {fmt(r,2)} · ρ = {fmt(rho,2)} · n = {n}", legend_bottom=True)
            show(fig, "scatter_ai_prod")
            st.markdown('<div class="chart-note">Bubble size = manufacturing share of employment. Small sample '
                        '(4 countries × survey waves): descriptive only, not causal.</div>', unsafe_allow_html=True)

    # 2.3 Dumbbell + gap evolution
    with right:
        mode = st.radio("Chart", ["Snapshot (dumbbell)", "Gap over time"], horizontal=True, key="dumb_mode")
        if mode.startswith("Snapshot"):
            d = df_m_filt[df_m_filt["year"] == focus_year].dropna(subset=["ai_small", "ai_large"]).sort_values("ai_large")
            fig = go.Figure()
            for _, row in d.iterrows():
                fig.add_trace(go.Scatter(x=[row["ai_small"], row["ai_large"]], y=[row["country_name"]] * 2, mode="lines",
                                         line=dict(color="#CBD5E1", width=6), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=d["ai_small"], y=d["country_name"], mode="markers", name="Small (10–49)",
                                     marker=dict(color="#3B82F6", size=15),
                                     hovertemplate="<b>%{y}</b><br>Small firms: %{x:.1f}%<extra></extra>"))
            fig.add_trace(go.Scatter(x=d["ai_large"], y=d["country_name"], mode="markers+text", name="Large (250+)",
                                     marker=dict(color="#EF4444", size=15),
                                     text=[f"+{g:.1f} pp" for g in d["ai_gap_large_small"]], textposition="middle right",
                                     hovertemplate="<b>%{y}</b><br>Large firms: %{x:.1f}%<extra></extra>"))
            fig.update_xaxes(title="AI adoption (%)", ticksuffix="%", range=[0, max(d["ai_large"].max() * 1.25, 10)] if len(d) else None)
            style(fig, 470, f"2.3 Small vs. large firms ({focus_year})", legend_bottom=True)
            show(fig, "dumbbell")
        else:
            fig = go.Figure()
            for c in selected_countries:
                s = df_m_filt[df_m_filt["country_name"] == c].dropna(subset=["ai_gap_large_small"]).sort_values("year")
                fig.add_trace(go.Scatter(
                    x=s["year"], y=s["ai_gap_large_small"], mode="lines+markers", name=c,
                    line=dict(color=COUNTRY_COLORS[c], width=3.5, dash="dash" if c == "EU-27 Average" else "solid"),
                    marker=dict(size=9), hovertemplate="%{y:.1f} pp",
                ))
            fig.update_xaxes(tickmode="array", tickvals=AI_YEARS, title="")
            fig.update_yaxes(title="Large − small adoption gap (pp)", rangemode="tozero")
            fig.update_layout(hovermode="x unified")
            style(fig, 470, "2.3 The firm-size gap keeps widening", legend_bottom=True)
            show(fig, "gap_time")

# ------------------------------------------------------------------------------
# TAB 3
# ------------------------------------------------------------------------------
with tab3:
    if show_notes:
        st.markdown(
            """<div class="story-box"><strong>Act III · The social filter.</strong> AI skills are increasingly requested
            in job ads, and vacancies remain tight in several economies. But does higher adoption go hand in hand with
            lower poverty risk? The connected trajectories below let you judge — with an honest look at the evidence.</div>""",
            unsafe_allow_html=True,
        )

    left, right = st.columns([1, 1.1])

    # 3.1 AI job postings
    with left:
        a, b = st.columns([1, 1.3])
        with a:
            owid_mode = st.radio("Display", ["Level (%)", "Index (2021 = 100)"], key="owid_mode")
        with b:
            owid_years = st.slider("Years", 2014, 2025, (2018, 2025), key="owid_years")
        d = df_o_filt.dropna(subset=["ai_job_postings_pct"]).copy()
        d = d[d["year"].between(*owid_years)]
        if owid_mode.startswith("Index"):
            base = df_owid_hist[df_owid_hist["year"] == 2021].set_index("country_name")["ai_job_postings_pct"]
            d = d[d["year"] >= 2021]
            d["value"] = d.apply(lambda r: r["ai_job_postings_pct"] / base.get(r["country_name"], np.nan) * 100, axis=1)
            ylab, suffix = "Index (2021 = 100)", ""
        else:
            d["value"] = d["ai_job_postings_pct"]
            ylab, suffix = "Share of online job postings (%)", "%"
        if d.empty:
            st.info("No job-postings data for this selection (EU-27 aggregate is not available in this dataset).")
        else:
            fig = go.Figure()
            for c in [x for x in selected_countries if x in d["country_name"].unique()]:
                s = d[d["country_name"] == c].sort_values("year")
                fig.add_trace(go.Scatter(x=s["year"], y=s["value"], mode="lines+markers", name=c,
                                         line=dict(color=COUNTRY_COLORS[c], width=3.5), marker=dict(size=8),
                                         hovertemplate="%{y:.2f}" + suffix))
            fig.update_xaxes(dtick=1, title="")
            fig.update_yaxes(title=ylab, ticksuffix=suffix if suffix else "")
            fig.update_layout(hovermode="x unified")
            style(fig, 450, "3.1 Wave of AI-skill demand in online job postings", legend_bottom=True)
            show(fig, "owid")
            st.markdown('<div class="chart-note">Each line is a separate country (shares are not additive). '
                        'France, Germany and Spain start in 2018; Italy in 2014. Source: Lightcast via AI Index 2026.</div>',
                        unsafe_allow_html=True)

    # 3.2 Connected scatter: AI vs poverty
    with right:
        incl_eu = st.checkbox("Include the EU-27 aggregate", value=False, key="conn_eu")
        pool = selected_countries if incl_eu else countries_only
        d = df_m_filt[df_m_filt["country_name"].isin(pool)].dropna(subset=["ai_total", "poverty_arop"]).sort_values(["country_name", "year"])
        if d.empty:
            st.info("Select at least one country.")
        else:
            fig = go.Figure()
            for c in [x for x in pool if x in d["country_name"].unique()]:
                s = d[d["country_name"] == c]
                col = COUNTRY_COLORS[c]
                fig.add_trace(go.Scatter(
                    x=s["ai_total"], y=s["poverty_arop"], mode="lines+markers+text", name=c,
                    line=dict(color=col, width=3), marker=dict(size=10, line=dict(color="white", width=1.5)),
                    text=s["year"].astype(str).str[2:].radd("'"), textposition="top center", textfont=dict(size=10),
                    customdata=s["year"],
                    hovertemplate=f"<b>{c} · %{{customdata}}</b><br>AI adoption: %{{x:.1f}}%<br>Poverty risk: %{{y:.1f}}%<extra></extra>",
                ))
                if len(s) >= 2:
                    fig.add_annotation(x=s["ai_total"].iloc[-1], y=s["poverty_arop"].iloc[-1], ax=s["ai_total"].iloc[-2],
                                       ay=s["poverty_arop"].iloc[-2], xref="x", yref="y", axref="x", ayref="y",
                                       showarrow=True, arrowhead=3, arrowsize=1.3, arrowwidth=2, arrowcolor=col)
            if not incl_eu and "EU-27 Average" in selected_countries:
                eu_pov_now = eu_val("poverty_arop", LATEST_AI_YEAR)
                if pd.notna(eu_pov_now):
                    fig.add_hline(y=eu_pov_now, line_dash="dot", line_color="#8B5CF6",
                                  annotation_text=f"EU-27 AROP {LATEST_AI_YEAR}: {eu_pov_now:.1f}%", annotation_position="bottom right")
            fig.update_xaxes(title="Enterprise AI adoption (%)", ticksuffix="%")
            fig.update_yaxes(title="At-risk-of-poverty rate (%)", ticksuffix="%")
            style(fig, 450, "3.2 Trickle-down test: AI adoption vs. poverty risk", legend_bottom=True)
            show(fig, "connected")
            r, rho, n = corr_stats(d["ai_total"], d["poverty_arop"])
            st.markdown(f'<div class="chart-note">Pooled correlation: r = {fmt(r,2)}, ρ = {fmt(rho,2)} (n = {n}). '
                        'Arrows show the last move; poverty is shaped by many other factors.</div>', unsafe_allow_html=True)

    left2, right2 = st.columns([1.1, 1])

    # 3.3 AROP long trend
    with left2:
        fig = go.Figure()
        for c in selected_countries:
            s = df_p_filt[df_p_filt["country_name"] == c].sort_values("year")
            fig.add_trace(go.Scatter(
                x=s["year"], y=s["poverty_arop"], mode="lines+markers", name=c,
                line=dict(color=COUNTRY_COLORS[c], width=3, dash="dash" if c == "EU-27 Average" else "solid"),
                marker=dict(size=7), hovertemplate="%{y:.1f}%",
            ))
        fig.add_vrect(x0=2022.5, x1=2025.5, fillcolor="#DBEAFE", opacity=0.35, line_width=0,
                      annotation_text="gen-AI era", annotation_position="top left", annotation_font_size=11)
        fig.update_xaxes(dtick=1, title="")
        fig.update_yaxes(ticksuffix="%", title="At-risk-of-poverty rate")
        fig.update_layout(hovermode="x unified")
        style(fig, 420, "3.3 Poverty risk in the long run (2016–2025)", legend_bottom=True)
        show(fig, "arop_trend")

    # 3.4 Vacancy rate
    with right2:
        jv_years = sorted(df_jvs_sec["year"].unique().tolist())
        if jv_years:
            jv_year = st.radio("Vacancy rate year", jv_years, index=len(jv_years) - 1, horizontal=True, key="jv_year")
            d = df_jvs_sec[(df_jvs_sec["year"] == jv_year) & df_jvs_sec["country_name"].isin(selected_countries)]
            fig = px.bar(
                d, x="country_name", y="job_vacancy_rate", color="group", barmode="group",
                category_orders={"country_name": selected_countries,
                                 "group": ["Industry & construction", "Industry & market services", "Whole economy"]},
                color_discrete_sequence=["#94A3B8", "#2563EB", "#1E3A8A"],
                labels={"country_name": "", "job_vacancy_rate": "Job vacancy rate (%)", "group": ""},
            )
            fig.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.2f}%<extra></extra>")
            fig.update_yaxes(ticksuffix="%")
            style(fig, 420, f"3.4 Labour-market tension: job vacancy rate ({jv_year})", legend_bottom=True)
            show(fig, "vacancy")
            st.markdown('<div class="chart-note">Eurostat quarterly data are only available from 2024 in this extract '
                        '(annual mean of unadjusted quarters, firms with 10+ employees). Spain is structurally low.</div>',
                        unsafe_allow_html=True)

    # 3.5 Before / after quadrant
    d_first = df_master[df_master["year"] == FIRST_AI_YEAR].set_index("geo")
    d_last = df_master[df_master["year"] == LATEST_AI_YEAR].set_index("geo")
    delta = pd.DataFrame({
        "d_ai": d_last["ai_total"] - d_first["ai_total"],
        "d_pov": d_last["poverty_arop"] - d_first["poverty_arop"],
        "d_gap": d_last["ai_gap_large_small"] - d_first["ai_gap_large_small"],
    }).dropna()
    delta["country_name"] = delta.index.map(COUNTRY_NAMES)
    dq = delta[delta["country_name"].isin(selected_countries)]
    if len(dq):
        fig = go.Figure()
        for _, r_ in dq.iterrows():
            c = r_["country_name"]
            fig.add_trace(go.Scatter(
                x=[r_["d_ai"]], y=[r_["d_pov"]], mode="markers+text", name=c, text=[c], textposition="top center",
                marker=dict(size=max(abs(r_["d_gap"]), 8) * 1.1, color=COUNTRY_COLORS[c], opacity=0.85,
                            symbol="diamond" if c == "EU-27 Average" else "circle", line=dict(color="white", width=2)),
                hovertemplate=(f"<b>{c}</b><br>Δ AI adoption: %{{x:+.1f}} pp<br>Δ poverty risk: %{{y:+.1f}} pp"
                               f"<br>Δ firm-size gap: {r_['d_gap']:+.1f} pp<extra></extra>"),
            ))
        fig.add_hline(y=0, line_color="#94A3B8")
        fig.add_vline(x=0, line_color="#94A3B8")
        fig.update_xaxes(title=f"Change in AI adoption {FIRST_AI_YEAR}→{LATEST_AI_YEAR} (pp)")
        fig.update_yaxes(title=f"Change in poverty risk {FIRST_AI_YEAR}→{LATEST_AI_YEAR} (pp)")
        fig.update_layout(showlegend=False)
        style(fig, 430, "3.5 Before / after: did faster AI adoption come with lower poverty risk? (bubble = Δ firm-size gap)")
        show(fig, "quadrant")
        st.markdown('<div class="chart-note">Below the horizontal line: poverty risk fell. Right of the vertical line: adoption rose. '
                    'Bubble size = increase in the large–small adoption gap.</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 4
# ------------------------------------------------------------------------------
with tab4:
    col_a, col_b = st.columns([1.15, 1])

    # Correlation matrix
    with col_a:
        method = st.radio("Correlation method", ["Pearson", "Spearman"], horizontal=True, key="corr_method")
        base_df = df_master[df_master["geo"] != "EU27_2020"][CORR_COLS].astype(float)
        corr = base_df.corr(method=method.lower())
        notna = base_df.notna().astype(int)
        n_mat = notna.T @ notna
        labels = [VAR_LABELS[c].split(" (")[0].replace("AI adoption – ", "AI ") for c in CORR_COLS]
        text = corr.round(2).astype(str).where(corr.notna(), "")
        fig = go.Figure(go.Heatmap(
            z=corr.values, x=labels, y=labels, zmin=-1, zmax=1, colorscale="RdBu_r", reversescale=False,
            text=text.values, texttemplate="%{text}", customdata=n_mat.values,
            hovertemplate="<b>%{y}</b> × <b>%{x}</b><br>" + method + " r = %{z:.2f}<br>n = %{customdata} obs.<extra></extra>",
            colorbar=dict(title="r", thickness=14),
        ))
        fig.update_yaxes(autorange="reversed")
        style(fig, 520, f"{method} correlation matrix · France, Germany, Spain, Italy (2021–2025)")
        show(fig, "corr")
        st.markdown('<div class="chart-note">Hover to see how many observations back each cell. '
                    'Cells with few observations (e.g. job vacancies: 2024–2025 only) are fragile.</div>', unsafe_allow_html=True)

    # Dynamic findings
    with col_b:
        st.markdown("### Answer to the research question")
        eu_ai_last = eu_val("ai_total", LATEST_AI_YEAR)
        gap_last = eu_val("ai_gap_large_small", LATEST_AI_YEAR)
        small_last, large_last = eu_val("ai_small", LATEST_AI_YEAR), eu_val("ai_large", LATEST_AI_YEAR)
        sec_eu = df_sec[(df_sec["geo"] == "EU27_2020") & (df_sec["year"] == LATEST_AI_YEAR)].dropna(subset=["ai_adoption"]).sort_values("ai_adoption")
        top2 = " and ".join(sec_eu["sector"].tail(2)[::-1]) if len(sec_eu) >= 5 else "ICT"
        low3 = ", ".join(sec_eu["sector"].head(3)) if len(sec_eu) >= 5 else "construction"
        st.success(
            f"**1. A fast-diffusing technology.** EU-27 firms using AI rose from {fmt(ai_base,1,'%')} ({FIRST_AI_YEAR}) to "
            f"{fmt(eu_ai_last,1,'%')} ({LATEST_AI_YEAR}), and AI skills are requested in a growing share of job ads "
            f"(global corporate AI investment: ${STANFORD_INVEST_BN:,.1f}B in 2025)."
        )
        st.warning(
            f"**2. A widening structural divide.** In {LATEST_AI_YEAR}, {fmt(large_last,1,'%')} of large EU firms use AI versus "
            f"{fmt(small_last,1,'%')} of small ones — a {fmt(gap_last,1,' pp')} gap, up from {fmt(gap_base,1,' pp')} in {FIRST_AI_YEAR}. "
            f"{top2} lead; {low3} lag."
        )
        r_pp, _, n_pp = corr_stats(base_df["ai_total"], base_df["prod_hourly_growth"])
        r_ap, _, n_ap = corr_stats(base_df["ai_total"], base_df["poverty_arop"])
        movers = delta[delta["country_name"] != "EU-27 Average"]
        up = ", ".join(f"{r_['country_name']} ({r_['d_pov']:+.1f} pp)" for _, r_ in movers[movers["d_pov"] > 0].iterrows()) or "none"
        down = ", ".join(f"{r_['country_name']} ({r_['d_pov']:+.1f} pp)" for _, r_ in movers[movers["d_pov"] <= 0].iterrows()) or "none"
        st.info(
            f"**3. No uniform social payoff — a mixed picture.** AI adoption rose everywhere between {FIRST_AI_YEAR} and "
            f"{LATEST_AI_YEAR}, yet poverty risk rose in: {up}; and fell in: {down} (EU-27 {fmt(pov_now - pov_base,1,' pp', plus=True)}). "
            f"Across the panel, AI adoption × poverty risk shows a {strength(r_ap)} link (r = {fmt(r_ap,2)}, n = {n_ap}); "
            f"AI adoption × hourly productivity growth shows a {strength(r_pp)} link (r = {fmt(r_pp,2)}, n = {n_pp}) that may simply "
            "reflect the common post-Covid cycle. None of this is causal."
        )
        st.markdown(
            "**Reading:** the evidence is consistent with *uneven diffusion* (by firm size and sector) rather than with a "
            "demonstrated social dividend — and it cannot show that AI itself raises or lowers poverty. Targeted SME support and "
            "reskilling are the natural policy levers to test next."
        )
        with st.expander("Methodological caveats"):
            st.markdown(
                "- **Correlation ≠ causation**: 4 countries × a few survey waves; no control variables.\n"
                "- **No 2022 AI survey wave**; 2021/2023 vs. 2024/2025 may not be strictly comparable.\n"
                "- **Productivity & ULC** are macro aggregates driven mostly by the post-Covid cycle and inflation.\n"
                "- **Job postings** (Lightcast) measure skill demand in online ads, not jobs created or destroyed.\n"
                "- **Job vacancy rate** is available from 2024 only in this extract.\n"
                "- **Investment ($581.7B)** is a global Stanford AI Index figure, not a European series."
            )

    st.markdown("---")
    st.markdown("### 🔎 Free explorer — build your own scatter")
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        ex = st.selectbox("X axis", list(VAR_LABELS.keys()), index=0, format_func=VAR_LABELS.get, key="ex_x")
    with e2:
        ey = st.selectbox("Y axis", list(VAR_LABELS.keys()), index=list(VAR_LABELS.keys()).index("poverty_arop"),
                          format_func=VAR_LABELS.get, key="ex_y")
    with e3:
        ecolor = st.radio("Colour by", ["Country", "Year"], horizontal=True, key="ex_color")
    with e4:
        etrend = st.checkbox("Trend line", value=True, key="ex_trend")
    de = df_m_filt[df_m_filt["geo"] != "EU27_2020"].dropna(subset=[ex, ey]).copy()
    if ex == ey:
        st.info("Choose two different variables.")
    elif len(de) < 3:
        st.info("Not enough overlapping observations for this pair (try other variables or more countries).")
    else:
        de["lbl"] = de["geo"] + " '" + de["year"].astype(str).str[2:]
        if ecolor == "Country":
            fig = px.scatter(de, x=ex, y=ey, color="country_name", color_discrete_map=COUNTRY_COLORS, text="lbl",
                             labels={ex: VAR_LABELS[ex], ey: VAR_LABELS[ey], "country_name": "Country"})
        else:
            fig = px.scatter(de, x=ex, y=ey, color="year", color_continuous_scale="Viridis", text="lbl",
                             labels={ex: VAR_LABELS[ex], ey: VAR_LABELS[ey], "year": "Year"})
        fig.update_traces(textposition="top center", marker=dict(size=13, line=dict(width=1.5, color="white")))
        if etrend and de[ex].nunique() > 1:
            m, b0 = np.polyfit(de[ex], de[ey], 1)
            xs = np.linspace(de[ex].min(), de[ex].max(), 20)
            fig.add_trace(go.Scatter(x=xs, y=m * xs + b0, mode="lines", name="OLS trend",
                                     line=dict(color="#475569", dash="dash", width=2), hoverinfo="skip"))
        r, rho, n = corr_stats(de[ex], de[ey])
        m1, m2, m3 = st.columns(3)
        m1.metric("Pearson r", fmt(r, 2))
        m2.metric("Spearman ρ", fmt(rho, 2))
        m3.metric("Observations", n)
        style(fig, 470, f"{VAR_LABELS[ey]} vs. {VAR_LABELS[ex]}", legend_bottom=ecolor == "Country")
        show(fig, "explorer")
        if n < 20:
            st.markdown('<div class="caveat">⚠️ Fewer than 20 observations: treat this as an illustration, not a statistical result.</div>',
                        unsafe_allow_html=True)

    with st.expander("📂 Inspect & download the consolidated master panel"):
        show_df(df_m_filt.round(2), hide_index=True)
        st.download_button(
            "⬇️ Download master panel (CSV)",
            df_m_filt.round(3).to_csv(index=False).encode("utf-8"),
            file_name="ai_europe_master_panel.csv",
            mime="text/csv",
        )
