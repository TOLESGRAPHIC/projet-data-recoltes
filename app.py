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

def fr(x, decimales=0):
    """Nombre à la française : espace pour les milliers, virgule pour les décimales."""
    texte = f"{x:,.{decimales}f}"
    return texte.replace(",", " ").replace(".", ",")


# ---------------------------------------------------------------- Indicateurs
production_totale = df["production_t"].sum()
valeur_totale = df["valeur_htg"].sum()
surface_totale = df["surface_ha"].sum()
par_culture = df.groupby("culture")["production_t"].sum().sort_values(ascending=False)
culture_n1 = par_culture.index[0]
part_n1 = par_culture.iloc[0] / production_totale * 100

k1, k2, k3, k4 = st.columns(4)
if production_totale >= 10_000:
    k1.metric("Production totale (milliers de tonnes)", fr(production_totale / 1000, 1))
else:
    k1.metric("Production totale (tonnes)", fr(production_totale))
if valeur_totale >= 1e9:
    k2.metric("Valeur totale (milliards de gourdes)", fr(valeur_totale / 1e9, 1))
else:
    k2.metric("Valeur totale (millions de gourdes)", fr(valeur_totale / 1e6, 1))
if surface_totale >= 10_000:
    k3.metric("Surface récoltée (milliers d'hectares)", fr(surface_totale / 1000, 1))
else:
    k3.metric("Surface récoltée (hectares)", fr(surface_totale))
k4.metric("Culture n°1 en tonnes", culture_n1)
k4.caption(f"{fr(part_n1, 1)} % de la production sélectionnée")

st.write("")