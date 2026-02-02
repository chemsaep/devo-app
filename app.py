import streamlit as st
import pandas as pd
from fpdf import FPDF
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo : Wassah Event", layout="wide", page_icon="🥐")

# --- 2. CSS (DESIGN PREMIUM) ---
st.markdown("""
    <style>
    /* Fond de page et police */
    .stApp { background-color: #FDFBF7; color: #4E342E; }
    
    /* Titres */
    h1, h2, h3 { 
        color: #5D4037 !important; 
        font-family: 'Playfair Display', serif;
        border-bottom: 2px solid #D7CCC8;
        padding-bottom: 10px;
    }

    /* Style des zones de texte */
    .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #4E342E !important;
        border: 2px solid #D7CCC8 !important;
        border-radius: 12px !important;
        padding: 15px !important;
        font-size: 16px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }

    /* Boutons personnalisés */
    .stButton>button {
        background: linear-gradient(145deg, #5D4037, #3E2723);
        color: white !important;
        border-radius: 50px !important;
        border: none !important;
        padding: 15px 30px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.2);
        color: #F7F3E8 !important;
    }

    /* Tableau éditable */
    div[data-testid="stDataFrame"] {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        border: 1px solid #E0E0E0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }

    /* Cartes d'info */
    .client-card {
        background-color: #F7F3E8;
        padding: 20px;
        border-left: 5px solid #5D4037;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIQUE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 20)
        self.set_text_color(93, 64, 55)
        self.cell(0, 15, 'WASSAH EVENT - DEVIS', 0, 1, 'C')
        self.ln(10)

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Bloc Client
    pdf.set_fill_color(247, 243, 232)
    pdf.cell(0, 10, "DESTINATAIRE", ln=True, fill=True)
    pdf.set_font("Arial", size=11)
    for ligne in client_info:
        pdf.cell(0, 7, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True)
    
    pdf.ln(10)
    
    # En-tête Tableau
    pdf.set_fill_color(93, 64, 55)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(100, 10, "Prestation", 1, 0, 'C', True)
    pdf.cell(30, 10, "Prix Unit.", 1, 0, 'C', True)
    pdf.cell(20, 10, "Qté", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    # Corps Tableau
    pdf.set_text_color(0, 0, 0)
    for _, row in df_panier.iterrows():
        pdf.cell(100, 10, str(row['Désignation']), 1)
        pdf.cell(30, 10, f"{row['Prix Unit.']:.2f}", 1, 0, 'R')
        pdf.cell(20, 10, str(row['Qté']), 1, 0, 'C')
        pdf.cell(40, 10, f"{row['Total']:.2f}", 1, 1, 'R')
        
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(150, 10, "TOTAL TTC : ", 0, 0, 'R')
    pdf.cell(40, 10, f"{total_ttc:.2f} EUR", 1, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. ANALYSE ---
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
                
                # Recherche intelligente (floue)
                for _, row in df_catalogue.iterrows():
                    if txt_produit in str(row['Produit']).lower():
                        produit_trouve = row['Produit']
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
st.title("🥐 Devo : Wassah Event")

try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("Fichier catalogue.csv introuvable.")
    st.stop()

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns([1, 1.2], gap="large")

with col1:
    st.subheader("1. Saisie du message")
    texte_input = st.text_area("Collez le message WhatsApp/Email ici :", height=250, placeholder="Moussa Diop\n06...\n- 2 box gourmande")
    
    if st.button("✨ Créer le Brouillon"):
        client, panier = analyser_texte(texte_input, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)

with col2:
    st.subheader("2. Finalisation du Devis")
    if not st.session_state['panier_df'].empty:
        # Affichage Client stylisé
        client_text = "<br>".join(st.session_state['client_info'])
        st.markdown(f'<div class="client-card"><b>Client :</b><br>{client_text}</div>', unsafe_allow_html=True)
        
        # Tableau éditable
        edited_df = st.data_editor(
            st.session_state['panier_df'],
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Prix Unit.": st.column_config.NumberColumn("Prix (€)", format="%.2f"),
                "Qté": st.column_config.NumberColumn("Qté", format="%d")
            }
        )
        
        edited_df["Total"] = edited_df["Prix Unit."] * edited_df["Qté"]
        grand_total = edited_df["Total"].sum()
        
        st.markdown(f"<h2 style='text-align:right; color:#5D4037;'>Total : {grand_total:.2f} €</h2>", unsafe_allow_html=True)
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, grand_total)
        
        st.download_button(
            label="📩 Télécharger le PDF Officiel",
            data=pdf_bytes,
            file_name="devis_wassah.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    else:
        st.info("Utilisez la zone de gauche pour commencer.")
