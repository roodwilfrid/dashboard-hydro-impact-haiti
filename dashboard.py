import pandas as pd
import unicodedata
import re
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

# =====================================================
# 1. Charger les données
# =====================================================

df_global = pd.read_csv("dataset_global.csv")

df_impacts = pd.read_excel("impacts_communes.xlsx")

# =====================================================
# 2. Nettoyer les noms de communes
# =====================================================

def normalize_name(name):

    if pd.isna(name):
        return name

    name = (
        unicodedata
        .normalize("NFKD", str(name))
        .encode("ascii", "ignore")
        .decode("utf-8")
    )

    name = name.lower()

    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    return name


df_global["commune_clean"] = (
    df_global["adm2_name"]
    .apply(normalize_name)
)

df_impacts["commune_clean"] = (
    df_impacts["adm2_name"]
    .apply(normalize_name)
)

# =====================================================
# 3. Nettoyer les événements
# =====================================================

df_global["event"] = (
    df_global["event"]
    .astype(str)
    .str.strip()
)

df_impacts["event"] = (
    df_impacts["event"]
    .astype(str)
    .str.strip()
)

# =====================================================
# 4. Calculer les scores d’impact
# =====================================================

impact_cols = ["C1", "C2", "C3", "C4", "C5"]

df_impacts[impact_cols] = (
    df_impacts[impact_cols]
    .apply(pd.to_numeric, errors="coerce")
    .fillna(0)
)

df_impacts["impact_score"] = (
    df_impacts[impact_cols]
    .sum(axis=1)
)

df_impacts["score_10"] = (
    df_impacts["impact_score"] / 2
)

# =====================================================
# 5. Fusion des données
# =====================================================

df_matrix = df_global.merge(
    df_impacts,
    on=["event", "commune_clean"],
    how="inner",
    suffixes=("_hydro", "_impact")
)

# =====================================================
# 6. Noms affichés des événements
# =====================================================

event_labels = {
    "Beryl_2024": "Ouragan Beryl (2024)",
    "Inondations_f_v_2022": "Inondations février 2022",
    "Inondations_juin_2023": "Inondations juin 2023",
    "Inondations_mars_2007": "Inondations mars 2007",
    "Intemperies_nov_2016": "Intempéries novembre 2016",
    "Irma": "Ouragan Irma",
    "Isaac": "Tempête Isaac",
    "Laura": "Tempête Laura",
    "Matthew": "Ouragan Matthew",
    "Sandy": "Ouragan Sandy",
    "Thomas": "Tempête Thomas"
}

# =====================================================
# 7. Configuration générale
# =====================================================

st.set_page_config(
    page_title="Dashboard hydro-impacts",
    layout="wide"
)

# =====================================================
# 8. Style CSS
# =====================================================

st.markdown(
    """
    <style>

    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 2.3rem;
        font-weight: 800;
        color: #1B2631;
    }

    [data-testid="stMetricLabel"] {
        font-size: 1.25rem;
        font-weight: 700;
        color: #2C3E50;
    }

    [data-testid="metric-container"] {
        padding: 10px 5px 10px 5px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 9. Titre général
# =====================================================

st.markdown(
    """
    <h1 style='text-align:center;
               font-size:42px;
               color:#1B2631;
               margin-bottom:0px;
               font-weight:700;'>

    Analyse des relations entre précipitations extrêmes
    et impacts observés en Haïti

    </h1>

    <p style='text-align:center;
              font-size:20px;
              color:#566573;
              margin-top:10px;
              margin-bottom:25px;'>

    Exploration hydroclimatique multi-événements
    à l’échelle communale pour l’appui aux systèmes
    d’alerte précoce et à l’anticipation des impacts

    </p>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 10. Sélection de l’événement
# =====================================================

event_list = sorted(
    df_matrix["event"]
    .dropna()
    .unique()
)

selected_event = st.sidebar.selectbox(
    "Choisir un événement",
    event_list,
    format_func=lambda x: event_labels.get(
        x,
        x.replace("_", " ").title()
    )
)

df_event = (
    df_matrix[
        df_matrix["event"] == selected_event
    ]
    .copy()
)

event_display = event_labels.get(
    selected_event,
    selected_event.replace("_", " ").title()
)

# =====================================================
# 11. Titre événement
# =====================================================

st.markdown(
    f"""
    <h2 style='font-size:30px;
               margin-bottom:12px;
               color:#2C3E50;
               font-weight:700;'>

    Événement analysé : {event_display}

    </h2>
    """,
    unsafe_allow_html=True
)

# =====================================================
# 12. Indicateurs clés
# =====================================================

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Communes analysées",
    df_event["commune_clean"].nunique()
)

col2.metric(
    "Score moyen /10",
    round(df_event["score_10"].mean(), 2)
)

col3.metric(
    "Score maximal /10",
    round(df_event["score_10"].max(), 2)
)

col4.metric(
    "Pluie max 24h",
    round(df_event["m_max_24h_7d"].max(), 1)
)

col5.metric(
    "Cumul max 7 jours",
    round(df_event["m_sum_7d"].max(), 1)
)

st.divider()

# =====================================================
# 13. Palette graphique
# =====================================================

impact_palette = {
    "Faible": "#2ECC71",
    "Modéré": "#F1C40F",
    "Moyen": "#E67E22",
    "Élevé": "#E74C3C",
    "Très élevé": "#8E44AD",
    "Low": "#2ECC71",
    "Moderate": "#F1C40F",
    "High": "#E74C3C",
    "Severe": "#8E44AD"
}

bar_palette = [
    "#3498DB",
    "#1ABC9C",
    "#F39C12",
    "#E74C3C",
    "#9B59B6"
]

line_color = "#1F77B4"

common_layout = dict(
    template="plotly_white",
    title_x=0.5,
    title_font=dict(
        size=22,
        color="#1B2631"
    ),
    margin=dict(
        l=25,
        r=25,
        t=60,
        b=40
    ),
    font=dict(
        size=14,
        color="#2C3E50"
    )
)

# =====================================================
# 14. Évolution moyenne des pluies
# =====================================================

rain_cols = [
    "m_rain_jm3",
    "m_rain_jm2",
    "m_rain_jm1",
    "m_rain_j",
    "m_rain_jp1",
    "m_rain_jp2",
    "m_rain_jp3"
]

rain_labels = {
    "m_rain_jm3": "J-3",
    "m_rain_jm2": "J-2",
    "m_rain_jm1": "J-1",
    "m_rain_j": "J",
    "m_rain_jp1": "J+1",
    "m_rain_jp2": "J+2",
    "m_rain_jp3": "J+3"
}

jour_order = [
    "J-3",
    "J-2",
    "J-1",
    "J",
    "J+1",
    "J+2",
    "J+3"
]

df_rain = df_event.melt(
    id_vars=["commune_clean"],
    value_vars=rain_cols,
    var_name="jour",
    value_name="pluie"
)

df_rain["jour"] = (
    df_rain["jour"]
    .map(rain_labels)
)

df_rain["jour"] = pd.Categorical(
    df_rain["jour"],
    categories=jour_order,
    ordered=True
)

df_rain_mean = (
    df_rain
    .groupby(
        "jour",
        as_index=False,
        observed=False
    )
    .agg(
        pluie_moyenne=("pluie", "mean")
    )
)

fig_rain = px.line(
    df_rain_mean,
    x="jour",
    y="pluie_moyenne",
    markers=True,
    title="Évolution moyenne des pluies",
    labels={
        "jour": "Jour autour de l’événement",
        "pluie_moyenne": "Pluie moyenne"
    }
)

fig_rain.update_traces(
    line=dict(
        color=line_color,
        width=4
    ),
    marker=dict(
        size=9,
        color="#E74C3C"
    )
)

fig_rain.update_layout(
    **common_layout,
    height=380,
    xaxis_title="Jour autour de l’événement",
    yaxis_title="Pluie moyenne"
)

# =====================================================
# 15. Pluie max 24h et score d’impact
# =====================================================

fig_scatter_24h = px.scatter(
    df_event,
    x="m_max_24h_7d",
    y="score_10",
    color="impact_class",
    size="m_sum_7d",
    hover_name="commune_clean",
    color_discrete_map=impact_palette,
    title="Pluie maximale 24h et score d’impact",
    labels={
        "m_max_24h_7d": "Pluie maximale 24h",
        "score_10": "Score d’impact /10",
        "impact_class": "Classe d’impact",
        "m_sum_7d": "Cumul 7 jours"
    }
)

fig_scatter_24h.update_traces(
    marker=dict(
        line=dict(
            width=1,
            color="white"
        ),
        opacity=0.85
    )
)

fig_scatter_24h.update_layout(
    **common_layout,
    height=380,
    legend=dict(
        title="Classe d’impact",
        orientation="h",
        yanchor="bottom",
        y=-0.12,
        xanchor="center",
        x=0.5,
        font=dict(size=12)
    )
)

# =====================================================
# 16. Profil moyen des impacts
# =====================================================

df_impact_mean = (
    df_event[impact_cols]
    .mean()
    .reset_index()
)

df_impact_mean.columns = [
    "critere",
    "score_moyen"
]

critere_labels = {
    "C1": "Pertes humaines",
    "C2": "Personnes affectées",
    "C3": "Maisons touchées",
    "C4": "Infrastructures",
    "C5": "Agriculture"
}

df_impact_mean["critere"] = (
    df_impact_mean["critere"]
    .map(critere_labels)
)

fig_impacts = px.bar(
    df_impact_mean,
    x="critere",
    y="score_moyen",
    color="critere",
    color_discrete_sequence=bar_palette,
    title="Profil moyen des impacts",
    labels={
        "critere": "Critère d’impact",
        "score_moyen": "Score moyen"
    }
)

fig_impacts.update_layout(
    **common_layout,
    height=380,
    showlegend=False,
    xaxis_tickangle=-15
)

# =====================================================
# 17. Corrélation pluie-impact
# =====================================================

corr_cols = [
    "m_max_24h_7d",
    "m_max_72h_7d",
    "m_sum_72h_ref",
    "m_sum_7d",
    "m_mean_wet_intensity_7d",
    "m_concentration_ratio_7d",
    "m_wet_days_7d",
    "score_10"
]

corr_labels = {
    "m_max_24h_7d": "Max 24h",
    "m_max_72h_7d": "Max 72h",
    "m_sum_72h_ref": "Cumul 72h",
    "m_sum_7d": "Cumul 7j",
    "m_mean_wet_intensity_7d": "Intensité moy.",
    "m_concentration_ratio_7d": "Concentration",
    "m_wet_days_7d": "Jours pluvieux",
    "score_10": "Impact /10"
}

corr_matrix = (
    df_event[corr_cols]
    .corr()
)

corr_matrix.rename(
    index=corr_labels,
    columns=corr_labels,
    inplace=True
)

fig_corr = go.Figure(
    data=go.Heatmap(
        z=corr_matrix.values,
        x=corr_matrix.columns,
        y=corr_matrix.index,
        text=round(corr_matrix, 2),
        texttemplate="%{text}",
        colorscale="RdBu_r",
        zmin=-1,
        zmax=1,
        colorbar=dict(title="Corr.")
    )
)

fig_corr.update_layout(
    **common_layout,
    title=dict(
        text="Corrélation entre pluie et impact",
        x=0.46,
        xanchor="center"
    ),
    height=380
)

# =====================================================
# 18. Affichage des graphiques
# =====================================================

row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.plotly_chart(
        fig_rain,
        use_container_width=True
    )

with row1_col2:
    st.plotly_chart(
        fig_scatter_24h,
        use_container_width=True
    )

row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.plotly_chart(
        fig_impacts,
        use_container_width=True
    )

with row2_col2:
    st.plotly_chart(
        fig_corr,
        use_container_width=True
    )

# =====================================================
# 19. Tableau final
# =====================================================

st.divider()

st.markdown(
    """
    <h2 style='font-size:26px;
               color:#1B2631;
               margin-bottom:10px;
               font-weight:650;'>

    Données détaillées de l’événement

    </h2>
    """,
    unsafe_allow_html=True
)

st.dataframe(
    df_event,
    use_container_width=True
)
