from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

VERT, BLEU, ROUGE = "#2E7D32", "#1565C0", "#C62828"

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

def fr_signe(x, decimales=1):
    """Nombre à la française avec son signe : +19,1 ou −32,2."""
    signe = "+" if x > 0 else "−" if x < 0 else ""
    return signe + fr(abs(x), decimales)


def liste_et(elements):
    """['a', 'b', 'c'] devient 'a, b et c'."""
    if len(elements) <= 1:
        return "".join(elements)
    return ", ".join(elements[:-1]) + " et " + elements[-1]


def pluriel(n, mot):
    return f"{n} {mot}" + ("s" if n > 1 else "")


def accord(n, singulier, pluriel_):
    """Choisit la forme du verbe : 0 ou 1 → singulier, plus → pluriel."""
    return singulier if n <= 1 else pluriel_


def montant(valeur_htg):
    """Une somme en gourdes, en milliards ou en millions selon sa taille."""
    if valeur_htg >= 1e9:
        return f"{fr(valeur_htg / 1e9, 1)} milliards de gourdes"
    return f"{fr(valeur_htg / 1e6, 1)} millions de gourdes"


def pour_altair(donnees):
    """Copie du tableau avec les colonnes de texte en type « object », lu sans problème par Altair."""
    d = donnees.reset_index(drop=True).copy()
    colonnes_texte = d.select_dtypes(exclude="number").columns
    return d.astype({colonne: "object" for colonne in colonnes_texte})


def barres(donnees, valeur, categorie, titre, titre_axe, couleur, formater, hauteur=300, bicolore=False):
    """Barres horizontales triées, avec la valeur écrite au bout de chaque barre."""
    d = pour_altair(donnees)
    d["etiquette"] = d[valeur].map(formater)
    mini, maxi = float(d[valeur].min()), float(d[valeur].max())
    bas = mini * 1.3 if mini < 0 else 0.0
    haut = maxi * 1.2 if maxi > 0 else 0.0
    if haut == bas:
        haut = bas + 1.0

    base = alt.Chart(d).encode(
        x=alt.X(f"{valeur}:Q", title=titre_axe, scale=alt.Scale(domain=[bas, haut])),
        y=alt.Y(f"{categorie}:N", sort="-x", title=None),
    )
    infobulle = [
        alt.Tooltip(f"{categorie}:N", title="Élément"),
        alt.Tooltip("etiquette:N", title=titre_axe),
    ]
    if bicolore:
        signe = alt.condition(f"datum.{valeur} >= 0", alt.value(VERT), alt.value(ROUGE))
        rectangles = base.mark_bar(cornerRadiusEnd=3).encode(color=signe, tooltip=infobulle)
    else:
        rectangles = base.mark_bar(color=couleur, cornerRadiusEnd=3).encode(tooltip=infobulle)
    texte_positif = (
        base.mark_text(align="left", dx=4).encode(text="etiquette:N").transform_filter(f"datum.{valeur} >= 0")
    )
    texte_negatif = (
        base.mark_text(align="right", dx=-4).encode(text="etiquette:N").transform_filter(f"datum.{valeur} < 0")
    )
    return (rectangles + texte_positif + texte_negatif).properties(title=titre, height=hauteur)


# ---------------------------------------------------------------- Onglets
onglet1, onglet2, onglet3, onglet4, onglet5 = st.tabs(
    [
        "1 · Poids des cultures",
        "2 · Rendements",
        "3 · Effet de la pluie",
        "4 · Évolution",
        "5 · Production par habitant",
    ]
)

# ---- 1. Quelles cultures pèsent le plus ?
with onglet1:
    st.subheader("Quelles cultures pèsent le plus, en tonnes puis en valeur ?")
    classement = df.groupby("culture")[["production_t", "valeur_htg"]].sum()
    classement["part_t"] = classement["production_t"] / classement["production_t"].sum() * 100
    classement["part_v"] = classement["valeur_htg"] / classement["valeur_htg"].sum() * 100
    classement = classement.reset_index()
    classement["valeur_mds"] = classement["valeur_htg"] / 1e9

    g1, g2 = st.columns(2)
    g1.altair_chart(
        barres(classement, "production_t", "culture", "Production en tonnes", "Production (t)", VERT, lambda v: fr(v)),
    )
    g2.altair_chart(
        barres(
            classement, "valeur_mds", "culture", "Valeur en milliards de gourdes", "Valeur (milliards de gourdes)",
            BLEU, lambda v: fr(v, 1),
        ),
    )

    ordre_t = classement.sort_values("production_t", ascending=False)["culture"].tolist()
    ordre_v = classement.sort_values("valeur_htg", ascending=False)["culture"].tolist()
    t1, v1 = ordre_t[0], ordre_v[0]
    ligne = classement.set_index("culture")
    if len(ordre_t) == 1:
        verdict = ""
    elif ordre_t == ordre_v:
        verdict = "Le classement ne change pas."
    elif t1 != v1:
        verdict = "Le classement change, et la première place change aussi."
    else:
        verdict = "La première place ne change pas, mais le reste du classement bouge."
    rang_t = {c: i + 1 for i, c in enumerate(ordre_t)}
    rang_v = {c: i + 1 for i, c in enumerate(ordre_v)}
    gains = {c: rang_t[c] - rang_v[c] for c in ordre_t}
    meilleur_gain = max(gains, key=gains.get)
    complement = ""
    if gains[meilleur_gain] > 0:
        prix = df.loc[df["culture"] == meilleur_gain, "prix_htg_kg"].iloc[0]
        complement = (
            f" **{meilleur_gain}** gagne {pluriel(gains[meilleur_gain], 'place')} en valeur "
            f"grâce à son prix ({fr(prix)} gourdes le kg)."
        )
    if len(ordre_t) == 1:
        st.info(
            f"**Ce qu'on en conclut :** **{t1}** est la seule culture sélectionnée : "
            f"{fr(ligne.loc[t1, 'production_t'])} t, soit {montant(ligne.loc[t1, 'valeur_htg'])}. "
            "Sélectionnez plusieurs cultures pour comparer leur poids."
        )
    else:
        st.info(
            f"**Ce qu'on en conclut :** en tonnes, **{t1}** domine ({fr(ligne.loc[t1, 'production_t'])} t, "
            f"{fr(ligne.loc[t1, 'part_t'], 1)} % du total) ; en valeur, c'est **{v1}** "
            f"({montant(ligne.loc[v1, 'valeur_htg'])}, {fr(ligne.loc[v1, 'part_v'], 1)} % du total). "
            f"{verdict}{complement}"
        )

# ---- 2. Où les rendements sont-ils les meilleurs ?
with onglet2:
    st.subheader("Où les rendements (tonnes par hectare) sont-ils les meilleurs, culture par culture ?")
    rendements = df.groupby(["departement", "culture"])[["production_t", "surface_ha"]].sum().reset_index()
    rendements["rendement"] = rendements["production_t"] / rendements["surface_ha"]
    rendements["ecart"] = rendements["rendement"] / rendements.groupby("culture")["rendement"].transform("mean")
    rendements["texte"] = rendements["rendement"].map(lambda v: fr(v, 2))
    d = pour_altair(rendements)

    base = alt.Chart(d).encode(
        x=alt.X("culture:N", title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("departement:N", title=None),
    )
    cases = base.mark_rect().encode(
        color=alt.Color(
            "ecart:Q",
            scale=alt.Scale(scheme="redyellowgreen", domain=[0.7, 1.3], clamp=True),
            legend=alt.Legend(title="Écart à la moyenne de la culture"),
        ),
        tooltip=[
            alt.Tooltip("departement:N", title="Département"),
            alt.Tooltip("culture:N", title="Culture"),
            alt.Tooltip("texte:N", title="Rendement (t/ha)"),
        ],
    )
    chiffres = base.mark_text(fontSize=12).encode(text="texte:N")
    st.altair_chart(
        (cases + chiffres).properties(
            title="Rendement (t/ha) par département et par culture", height=max(120, 38 * d["departement"].nunique())
        ),
    )
    st.caption(
        "Vert : au-dessus de la moyenne de la culture ; rouge : en dessous. Case vide : culture absente du département. "
        "Chaque culture est comparée à elle-même, car une banane (7 t/ha) et un haricot (0,7 t/ha) n'ont pas la même échelle."
    )

    meilleurs = rendements.loc[rendements.groupby("culture")["rendement"].idxmax()].sort_values("culture")
    phrases = [f"**{r.culture}** : {r.departement} ({fr(r.rendement, 2)} t/ha)" for r in meilleurs.itertuples()]
    if rendements["departement"].nunique() == 1:
        introduction = "avec un seul département sélectionné, voici ses rendements."
    elif len(meilleurs) == 1:
        introduction = "voici le département où cette culture rend le mieux."
    else:
        introduction = "les meilleurs rendements dépendent de la culture."
    st.info(f"**Ce qu'on en conclut :** {introduction} {' ; '.join(phrases)}.")

# ---- 3. La pluie explique-t-elle les rendements ?
with onglet3:
    st.subheader("La pluie explique-t-elle les rendements ? Pour quelles cultures ?")
    correlations = {}
    for nom, groupe in df.groupby("culture"):
        if len(groupe) >= 3 and groupe["pluie_mm"].nunique() > 1 and groupe["rendement_t_ha"].nunique() > 1:
            correlations[nom] = groupe["rendement_t_ha"].corr(groupe["pluie_mm"])

    graphiques = []
    for nom in sorted(df["culture"].unique()):
        groupe = df[df["culture"] == nom].copy()
        groupe["pluie_txt"] = groupe["pluie_mm"].map(lambda v: fr(v))
        groupe["rendement_txt"] = groupe["rendement_t_ha"].map(lambda v: fr(v, 2))
        titre = f"{nom} (r = {fr(correlations[nom], 2)})" if nom in correlations else nom
        base = alt.Chart(pour_altair(groupe))
        axe_x = alt.X("pluie_mm:Q", title="Pluie de la saison (mm)", scale=alt.Scale(zero=False))
        axe_y = alt.Y("rendement_t_ha:Q", title="Rendement (t/ha)", scale=alt.Scale(zero=False))
        points = base.mark_circle(size=45, opacity=0.7, color=BLEU).encode(
            x=axe_x,
            y=axe_y,
            tooltip=[
                alt.Tooltip("departement:N", title="Département"),
                alt.Tooltip("annee:O", title="Année"),
                alt.Tooltip("saison:N", title="Saison"),
                alt.Tooltip("pluie_txt:N", title="Pluie (mm)"),
                alt.Tooltip("rendement_txt:N", title="Rendement (t/ha)"),
            ],
        )
        droite = (
            base.transform_regression("pluie_mm", "rendement_t_ha")
            .mark_line(color=ROUGE, size=2)
            .encode(x=axe_x, y=axe_y)
        )
        graphiques.append(alt.layer(points, droite).properties(title=titre, width=190, height=190))
    st.altair_chart(alt.concat(*graphiques, columns=4))
    st.caption("Un point = un département, une saison et une année. Droite rouge : tendance. r : corrélation entre la pluie et le rendement.")

    if correlations:
        tableau = (
            pd.DataFrame({"Culture": list(correlations), "r": list(correlations.values())})
            .assign(part=lambda t: t["r"] ** 2 * 100)
            .sort_values("r", ascending=False)
        )
        fort = tableau.iloc[0]
        faible = tableau.iloc[-1]
        meme_sens = int((tableau["r"] > 0).sum())
        if len(tableau) == 1:
            st.info(
                f"**Ce qu'on en conclut :** pour **{fort['Culture']}**, r = {fr(fort['r'], 2)} : la pluie « explique » "
                f"environ {fr(fort['part'])} % des écarts de rendement. "
                "Une corrélation n'est pas une preuve de cause : le sol, les semences ou l'irrigation comptent aussi."
            )
        else:
            st.info(
                f"**Ce qu'on en conclut :** le lien entre pluie et rendement est le plus fort pour **{fort['Culture']}** "
                f"(r = {fr(fort['r'], 2)}, la pluie « explique » environ {fr(fort['part'])} % des écarts de rendement) "
                f"et le plus faible pour **{faible['Culture']}** (r = {fr(faible['r'], 2)}, environ {fr(faible['part'])} %). "
                f"{pluriel(meme_sens, 'culture')} sur {len(tableau)} "
                f"{accord(meme_sens, 'va', 'vont')} dans le même sens que la pluie. "
                "Une corrélation n'est pas une preuve de cause : le sol, les semences ou l'irrigation comptent aussi."
            )
    else:
        st.info("Pas assez de points pour mesurer le lien entre la pluie et le rendement avec ces filtres.")

# ---- 4. Quelles cultures progressent ou reculent ?
with onglet4:
    annees_presentes = sorted(int(a) for a in df["annee"].unique())
    if len(annees_presentes) < 2:
        st.subheader("Quelles cultures progressent ou reculent ?")
        st.info("Sélectionnez au moins deux années dans la barre latérale pour comparer une évolution.")
    else:
        debut, fin = annees_presentes[0], annees_presentes[-1]
        st.subheader(f"Quelles cultures progressent ou reculent entre {debut} et {fin} ?")
        production = df.pivot_table(index="culture", columns="annee", values="production_t", aggfunc="sum")
        surface = df.pivot_table(index="culture", columns="annee", values="surface_ha", aggfunc="sum")
        evolution = pd.DataFrame(
            {
                "variation_production": (production[fin] / production[debut] - 1) * 100,
                "variation_surface": (surface[fin] / surface[debut] - 1) * 100,
            }
        ).dropna().reset_index()

        if evolution.empty:
            st.info("Aucune culture n'est présente aux deux dates avec ces filtres.")
        else:
            h1, h2 = st.columns(2)
            h1.altair_chart(
                barres(
                    evolution, "variation_production", "culture", f"Production : variation {debut} → {fin} (%)",
                    "Variation de la production (%)", VERT, lambda v: fr_signe(v) + " %", bicolore=True,
                ),
            )
            h2.altair_chart(
                barres(
                    evolution, "variation_surface", "culture", f"Surface cultivée : variation {debut} → {fin} (%)",
                    "Variation de la surface (%)", "#78909C", lambda v: fr_signe(v) + " %", bicolore=True,
                ),
            )
            tri = evolution.sort_values("variation_production")
            pire, meilleure = tri.iloc[0], tri.iloc[-1]
            hausses = int((evolution["variation_production"] > 0).sum())
            baisses = int((evolution["variation_production"] < 0).sum())
            total_debut = production[debut].sum()
            total_fin = production[fin].sum()
            total = (
                f"Au total, la production passe de {fr(total_debut)} t à {fr(total_fin)} t "
                f"({fr_signe((total_fin / total_debut - 1) * 100)} %)."
            )
            if len(evolution) == 1:
                st.info(
                    f"**Ce qu'on en conclut :** entre {debut} et {fin}, la production de **{pire['culture']}** varie de "
                    f"{fr_signe(pire['variation_production'])} % et sa surface cultivée de "
                    f"{fr_signe(pire['variation_surface'])} %. {total}"
                )
            else:
                if meilleure["variation_production"] >= 0:
                    haut = f"**{meilleure['culture']}** progresse le plus ({fr_signe(meilleure['variation_production'])} %)"
                else:
                    haut = f"**{meilleure['culture']}** recule le moins ({fr_signe(meilleure['variation_production'])} %)"
                if pire["variation_production"] < 0:
                    bas = f"**{pire['culture']}** recule le plus ({fr_signe(pire['variation_production'])} %)"
                else:
                    bas = f"**{pire['culture']}** progresse le moins ({fr_signe(pire['variation_production'])} %)"
                st.info(
                    f"**Ce qu'on en conclut :** entre {debut} et {fin}, {pluriel(hausses, 'culture')} "
                    f"{accord(hausses, 'progresse', 'progressent')} et {pluriel(baisses, 'culture')} "
                    f"{accord(baisses, 'recule', 'reculent')}. {haut}, {bas}, et sa surface cultivée varie de "
                    f"{fr_signe(pire['variation_surface'])} % sur la même période. {total}"
                )