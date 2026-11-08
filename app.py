from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="Les récoltes agricoles", page_icon="🌾", layout="wide")

# ---------------------------------------------------------------- Données
@st.cache_data
def charger():
    return pd.read_csv(DOSSIER / "recoltes_propre.csv")


complet = charger()

# ---------------------------------------------------------------- En-tête
st.title("🌾 Les récoltes agricoles")
st.markdown(
    "Une direction départementale de l'agriculture (fictive) suit les récoltes de 10 départements de 2023 à 2025, "
    "par saison et par culture, avec la pluie tombée pendant chaque saison. "
    "Ce tableau de bord répond au ministère : quelles cultures pèsent le plus, où les rendements sont les meilleurs, "
    "et la pluie explique-t-elle les mauvaises années ?"
)
st.caption(
    "Source : direction départementale de l'agriculture (données fictives), fichiers récoltes, cultures, pluies et "
    "départements, nettoyés et assemblés dans exploration.ipynb. "
    "Projet final, Python pour l'analyse de données, ESIH 2026."
)

# ---------------------------------------------------------------- Filtres
st.sidebar.header("Filtres")
st.sidebar.caption("Les indicateurs et tous les graphiques s'adaptent à ces choix.")

annees_dispo = [int(a) for a in sorted(complet["annee"].unique())]
annees = st.sidebar.multiselect("Années", annees_dispo, default=annees_dispo)
saison = st.sidebar.selectbox("Saison", ["Toutes", "Printemps", "Automne"])
departements_dispo = sorted(complet["departement"].unique())
departements_choisis = st.sidebar.multiselect("Départements", departements_dispo, default=departements_dispo)
cultures_dispo = sorted(complet["culture"].unique())
cultures_choisies = st.sidebar.multiselect("Cultures", cultures_dispo, default=cultures_dispo)

df = complet[
    complet["annee"].isin(annees)
    & complet["departement"].isin(departements_choisis)
    & complet["culture"].isin(cultures_choisies)
]
if saison != "Toutes":
    df = df[df["saison"] == saison]

st.sidebar.divider()
st.sidebar.caption(f"{len(df)} lignes sur {len(complet)} sélectionnées.")

if df.empty:
    st.warning("Aucune donnée pour ces filtres : choisissez au moins une année, un département et une culture.")
    st.stop()

# Aperçu provisoire, remplacé à l'étape suivante
st.dataframe(df.head(10), hide_index=True)