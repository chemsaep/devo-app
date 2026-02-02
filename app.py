import streamlit as st
import pandas as pd
import re
from fpdf import FPDF

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Devo Pro", layout="wide")

# --- 2. MENU DE CONFIGURATION (SIDEBAR) ---
st.sidebar.title("⚙️ Configuration Pro")

# Section 1 : Identité visuelle
st.sidebar.subheader("Identité Visuelle")
uploaded_bg = st.sidebar.file_uploader("Télécharger votre fond de devis (PNG/JPG)", type=["png", "jpg", "jpeg"])
# Si l'utilisateur n'a rien mis, on garde ton fond par défaut
fond_final = uploaded_bg if uploaded_bg else "fond_devis.png"

# Section 2 : Informations de l'entreprise
st.sidebar.subheader("Infos Entreprise")
nom_pro = st.sidebar.text_input("Nom de l'entreprise", "Wassah Event")
contact_pro = st.sidebar.text_input("Contact (Nom & Tel)", "Ward - 06.65.62.00.92")
insta_pro = st.sidebar.text_input("Instagram", "@wassah.event")
lieu_pro = st.sidebar.text_input("Zone d'intervention", "94")

# Section 3 : Catalogue
st.sidebar.subheader("Gestion des prix")
uploaded_catalog = st.sidebar.file_uploader("Importer un catalogue CSV", type=["csv"])
if uploaded_catalog:
    df_catalogue = pd.read_csv(uploaded_catalog)
else:
    # Par défaut on essaie de charger ton catalogue actuel
    try:
        df_catalogue = pd.read_csv("catalogue.csv")
    except:
        df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# On permet même de modifier le catalogue en direct !
st.sidebar.write("Modifier vos tarifs :")
df_catalogue = st.sidebar.data_editor(df_catalogue, num_rows="dynamic")

# Section 4 : Conditions de vente
st.sidebar.subheader("Conditions Légales")
cond_acompte = st.sidebar.text_area("Conditions d'acompte", "Paiement possible en 2 fois (Acompte de 50% à payer lors de la réservation)")
cond_annulation = st.sidebar.text_area("Conditions d'annulation", "Aucun remboursement en cas d'annulation moins de 7 jours avant")
