import streamlit as st
import pandas as pd
from fpdf import FPDF
import re
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo - Wassah Event", layout="wide", page_icon="🥐")

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

# --- 3. FONCTION PDF AVEC FOND PERSONNALISÉ ---
class PDF(FPDF):
    def header(self):
        # Vérifie si l'image de fond existe
        if os.path.exists("fond_devis.png"):
            # Affiche l'image en plein écran (x=0, y=0, largeur=210, hauteur=297)
            self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        else:
            # Si pas d'image, on garde l'en-tête texte par défaut (sécurité)
            self.set_font('Arial', 'B', 24)
            self.set_text_color(93, 64, 55)
            self.cell(0, 10, 'DEVIS', 0, 1, 'C')
            self.set_font('Arial', '', 12)
            self.cell(0, 10, 'Wassah Event', 0, 1, 'C')
            self.ln(20)

    def footer(self):
        # On écrit le numéro de page tout en bas
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # --- REGLAGE DE LA HAUTEUR DE DÉPART ---
    # C'est ICI qu'on décide où commence le texte pour ne pas écrire sur le logo
    # Si ton logo prend beaucoup de place, augmente ce chiffre (ex: 80 ou 100)
    pdf.set_y(60) 
    
    # --- BLOC CLIENT ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Devis pour :", ln=True)
    
    pdf.set_font("Arial", '', 11)
    # Fond légèrement transparent/beige pour que le texte client ressorte bien sur l'image
    pdf.set_fill_color(255, 255, 255) 
    
    infos_str = ""
    for ligne in client_info:
        infos_str += ligne + "\n"
    
    infos_str = infos_str.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 6, infos_str, fill=True, border=1) # Bordure fine pour faire propre
    pdf.ln(10)
    
    # --- TABLEAU ---
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 218, 208)
    pdf.cell(100, 10, "Prestations", 1, 0, 'L', True)
    pdf.cell(30, 10, "Prix Unit.", 1, 0, 'C', True)
    pdf.cell(20, 10, "Qté", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    pdf.set_font("Arial", size=11)
    # Fond blanc pour les lignes du tableau pour lisibilité max
    pdf.set_fill_color(255, 255, 255)
    
    for index, row in df_panier.iterrows():
        nom = str(row['Désignation']).encode('latin-1', 'replace').decode('latin-1')
        prix = float(row['Prix Unit.'])
        qte = int(row['Qté'])
        total_ligne = float(row['Total'])
        
        pdf.cell(100, 10, nom, 1, 0, 'L', True)
        pdf.cell(30, 10, f"{prix:.2f}", 1, 0, 'R', True)
        pdf.cell(20, 10, str(qte), 1, 0, 'C', True)
        pdf.cell(40, 10, f"{total_ligne:.2f}", 1, 1, 'R', True)
    
    pdf.ln(5)
    
    # --- TOTAL ---
    pdf.set_font("Arial", 'B', 14)
    # Petit fond blanc sous le total pour qu'il soit bien visible
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(150, 10, "TOTAL A PAYER :", 0, 0, 'R')
    pdf.cell(40, 10, f"{total_ttc:.2f} EUR", 1, 1, 'R', True)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. ANALYSE (MOTEUR) ---
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
st.title("🥐 Devo : Wassah Event")

try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("Catalogue introuvable")
    st.stop()

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. La Demande")
    exemple = """Client : Moussa Diop
Date : 08/11/2025
Lieu : 94

- 2 box gourmande
- 1 westaf 100"""
    texte_input = st.text_area("Zone de texte :", height=250, placeholder=exemple)
    if st.button("✨ Créer le Brouillon"):
        client, panier = analyser_texte(texte_input, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)

with col2:
    st.subheader("2. Le Devis Final")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], num_rows="dynamic", use_container_width=True)
        edited_df["Total"] = edited_df["Prix Unit."] * edited_df["Qté"]
        grand_total = edited_df["Total"].sum()
        
        st.markdown(f"<h3 style='text-align: right; color: #5D4037;'>Total : {grand_total:.2f} €</h3>", unsafe_allow_html=True)
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, grand_total)
        st.download_button("📄 Télécharger le PDF (Sur Fond Perso)", pdf_bytes, "devis_wassah.pdf", "application/pdf", type="primary")
