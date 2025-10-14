import streamlit as st
import polars as pl
import pandas as pd

st.set_page_config(page_title="Cartographie ETP sur 10 ans, TCD à la demande", layout="centered")

st.title("📊 Tableaux croisés dynamiques")

st.markdown("""
    <style>
    body {
        background-color: #0e1117;
        color: #fafafa;
    }
    [data-testid="stAppViewContainer"] {
        background-color: #0e1117;
    }
    [data-testid="stHeader"], [data-testid="stSidebar"] {
        background-color: #111;
    }
    [data-testid="stMarkdownContainer"] {
        color: #fafafa;
    }
    </style>
""", unsafe_allow_html=True)

# === Jeu de données exemple ===


st.subheader("⚙️ Paramètres du tableau croisé")

# --- 1️⃣ Lire le fichier Excel via Polars ---
df = pl.read_excel("dataf.xlsx")
df = df.fill_nan(0)
df = df.fill_null(0)

# --- Convertir en Pandas uniquement pour les widgets ---
df_pd = df.to_pandas()

st.title("📊 Tableau croisé interactif")

# --- Initialiser session_state ---
if "annee_sel" not in st.session_state:
    st.session_state.annee_sel = []
if "format_sel" not in st.session_state:
    st.session_state.format_sel = []

# --- 2️⃣ Premier multiselect : Années ---
annee_options = df_pd["Année"].dropna().unique().tolist()

st.session_state.annee_sel = st.multiselect(
    "Choisir année",
    options=annee_options,
    default=st.session_state.annee_sel
)

# --- Filtrer le DataFrame Polars selon la sélection ---
if st.session_state.annee_sel:
    df_filtered = df.filter(pl.col("Année").is_in(st.session_state.annee_sel))
else:
    df_filtered = df

# --- 3️⃣ Deuxième multiselect : Formats dépendants ---
# On convertit df_filtered en Pandas juste pour le widget
df_filtered_pd = df_filtered.to_pandas()

if st.session_state.annee_sel:
    format_options = df_filtered_pd["format_pdt"].dropna().unique().tolist()
else:
    format_options = []

st.session_state.format_sel = st.multiselect(
    "Choisir format (dépend de l'année)",
    options=format_options,
    default=st.session_state.format_sel
)

# --- Filtrer selon la sélection du 2e widget ---
if st.session_state.format_sel:
    df_filtered = df_filtered.filter(pl.col("format_pdt").is_in(st.session_state.format_sel))

#Vérifier les colonnes numériques
def is_numeric_dtype_polars(dtype) -> bool:
    """
    Vérifie si un type Polars est numérique.
    """
    numeric_types = (
        pl.Int8, pl.Int16, pl.Int32, pl.Int64,
        pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64,
        pl.Float32, pl.Float64
    )
    return dtype in numeric_types

numeric_cols = [c for c, t in zip(df.columns, df.dtypes) if is_numeric_dtype_polars(t)]
print(numeric_cols)

# === Sélecteurs dynamiques ===
df_pandas = df_filtered.to_pandas()
cols = df_filtered.columns
index_cols = st.multiselect("🧩 Colonnes de lignes (index)", cols, default=["Cat. LOLF"])
columns_col = st.multiselect("📅 Colonne de pivot (colonnes)", cols, default=["Année", "format_pdt"])
values_col = st.selectbox("💰 Valeur à agréger", cols, index=3)
agg_func = st.selectbox("🧮 Fonction d’agrégation", ["count"], index=0)

# === Création du pivot pandas ===
if index_cols and columns_col and values_col:
    try:
        if df_filtered.is_empty():
            st.warning("⚠️ Le DataFrame filtré est vide. Veuillez ajuster les filtres.")
        else:
            pivot = pd.pivot_table(
                df_pandas,
                index=index_cols,
                columns=columns_col,
                values=values_col,
                aggfunc=agg_func,
                fill_value=None,
                margins=False
            )

            # === Conversion en HTML (multi-index préservé) ===
            pivot = pivot.fillna(0)
            html_table = pivot.to_html(classes="dark-table", border=0)

            # === CSS Sombre scrollable ===
            st.markdown("""
            <style>
            .dark-table {
                display: block;
                max-height: 450px;
                overflow-y: auto;
                border: 1px solid #555;
                border-radius: 6px;
                background-color: #111;
                color: #f0f0f0;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 15px;
                text-align: right;
            }
            .dark-table th, .dark-table td {
                border: 1px solid #333;
                padding: 6px 10px;
            }
            .dark-table th {
                background-color: #222;
                color: #00bfff;
                position: sticky;
                top: 0;
                z-index: 2;
                text-align: center;
            }
            .dark-table tr:nth-child(even) {
                background-color: #1a1a1a;
            }
            .dark-table tr:hover {
                background-color: #003366;
                transition: 0.3s;
            }
            </style>
            """, unsafe_allow_html=True)

            # === Affichage du tableau ===
            st.subheader("📈 Résultat du tableau croisé")
            st.markdown(html_table, unsafe_allow_html=True)

            # === Bouton de téléchargement HTML ===
            st.download_button(
                label="📥 Télécharger le tableau HTML",
                data=html_table,
                file_name="pivot_multiindex_sombre.html",
                mime="text/html"
            )

    except Exception as e:
        st.error(f"Erreur lors de la création du pivot : {e}")

else:
    st.info("👉 Sélectionne au moins une colonne d’index, une colonne de pivot et une valeur à agréger.")


