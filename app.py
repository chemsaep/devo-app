import streamlit as st
import pandas as pd
from fpdf import FPDF
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo", layout="wide", page_icon="🥐")

# --- 2. CSS (DESIGN) ---
st.markdown("""
    <style>
    .stApp { background-color: #F7F3E8; color: #4E342E; }
    h1, h2, h3 { color: #5D4037 !important; }
    .stTextArea textarea { background-color: #FFFFFF; color: #4E342E; border: 1px solid #D7CCC8; }
    .stButton>button { background-color: #D7CCC8; color: #3E2723; border-radius: 8px; border: none; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #BCAAA4; color: white; }
    div[data-testid="stDataFrame"] { background-color: white; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FONCTION PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.set_text_color(93, 64, 55)
        self.cell(0, 10, 'WASSAH EVENT - DEVIS', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(0, 0, 0)

    # Infos Client
    pdf.set_fill_color(247, 243, 232)
    pdf.cell(0, 10, txt="INFORMATIONS CLIENT", ln=True, align='L', fill=True)
    pdf.ln(2)

    for ligne in client_info:
        ligne_propre = str(ligne).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 7, txt=ligne_propre, ln=True)

    pdf.ln(10)

    # Tableau
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(215, 204, 200)
    pdf.cell(100, 10, "Description", 1, 0, 'L', True)
    pdf.cell(30, 10, "Prix Unit.", 1, 0, 'C', True)
    pdf.cell(20, 10, "Qte", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)

    pdf.set_font("Arial", size=12)
    # On itère sur le DataFrame final (celui qui a été modifié)
    for index, row in df_panier.iterrows():
        nom = str(row['Désignation']).encode('latin-1', 'replace').decode('latin-1')
        prix = float(row['Prix Unit.'])
        qte = int(row['Qté'])
        total_ligne = float(row['Total'])

        pdf.cell(100, 10, nom, 1)
        pdf.cell(30, 10, f"{prix:.2f}", 1, 0, 'R')
        pdf.cell(20, 10, str(qte), 1, 0, 'C')
        pdf.cell(40, 10, f"{total_ligne:.2f}", 1, 1, 'R')

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(150, 10, "TOTAL A PAYER :", 0, 0, 'R')
    pdf.cell(40, 10, f"{total_ttc:.2f} EUR", 1, 1, 'R')

    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. ANALYSE (IA/REGEX) ---
def analyser_texte(texte, df_catalogue):
    lignes = texte.split('\n')
    infos_client = []
    panier_detecte = []

    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne: continue

        if ligne.startswith("-"):
            commande_brute = ligne.replace("-", "").strip()
            match_qte = re.match(r"(\d+)\s*(.*)", commande_brute)
            if match_qte:
                qte = int(match_qte.group(1))
                txt_produit = match_qte.group(2).lower()

                produit_trouve = None
                prix_trouve = 0.0

                for index, row in df_catalogue.iterrows():
                    nom_catalogue = str(row['Produit'])
                    if txt_produit in nom_catalogue.lower():
                        produit_trouve = nom_catalogue
                        prix_trouve = float(row['Prix'])
                        break

                if produit_trouve:
                    panier_detecte.append({"Désignation": produit_trouve, "Prix Unit.": prix_trouve, "Qté": qte})
                else:
                    panier_detecte.append({"Désignation": f"[?] {txt_produit}", "Prix Unit.": 0.0, "Qté": qte})
        else:
            infos_client.append(ligne)

    return infos_client, panier_detecte

# --- 5. INTERFACE ---
st.title("Devo   ")

try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("Catalogue introuvable")
    st.stop()

# Initialisation du Session State
if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns([1, 1.2]) # Colonne de droite un peu plus large

with col1:
    st.subheader("1. La Demande")
    exemple = "Moussa Diop\n06 12 34 56 78\nSaint-Denis\n\n- 2 box gourmande\n- 1 westaf 100"
    texte_input = st.text_area("Coller le message ici :", height=200, placeholder=exemple)

    if st.button("✨ Généner mon devis "):
        client, panier = analyser_texte(texte_input, df_catalogue)
        st.session_state['client_info'] = client
        # On crée un DataFrame Pandas
        st.session_state['panier_df'] = pd.DataFrame(panier)

with col2:
    st.subheader("2. Le Devis Final (Modifiable)")

    if not st.session_state['panier_df'].empty:
        # Affichage Client
        st.info(f"👤 Client : {' '.join(st.session_state['client_info'][:1])}")

        # --- TABLEAU ÉDITABLE ---
        # data_editor permet de modifier les valeurs directement !
        edited_df = st.data_editor(
            st.session_state['panier_df'],
            num_rows="dynamic", # Permet d'ajouter/supprimer des lignes
            use_container_width=True,
            column_config={
                "Prix Unit.": st.column_config.NumberColumn(format="%.2f €"),
                "Qté": st.column_config.NumberColumn(format="%d"),
            }
        )

        # --- RE-CALCUL EN TEMPS RÉEL ---
        # On calcule le total ligne par ligne en fonction des MODIFICATIONS
        edited_df["Total"] = edited_df["Prix Unit."] * edited_df["Qté"]

        grand_total = edited_df["Total"].sum()

        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        c2.markdown(f"<h2 style='color:#5D4037; text-align:right'>{grand_total:.2f} €</h2>", unsafe_allow_html=True)

        # --- BOUTON FINAL ---
        # Le PDF est généré à partir de 'edited_df' (la version modifiée)
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, grand_total)

        st.download_button(
            label="✅ Valider et Télécharger le PDF Final",
            data=pdf_bytes,
            file_name="devis_final.pdf",
            mime="application/pdf",
            type="primary"
        )

    else:

        st.warning("En attente d'analyse...")
