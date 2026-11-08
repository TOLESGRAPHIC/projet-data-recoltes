from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="Les récoltes agricoles", page_icon="🌾", layout="wide")

# Données
@st.cache_data
def charger():
    return pd.read_csv(DOSSIER / "recoltes_propre.csv")


complet = charger()

# En-tête
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


st.dataframe(complet.head(10), hide_index=True)