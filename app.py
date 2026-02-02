import streamlit as st
import pandas as pd
from fpdf import FPDF
import re

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Devo : Wassah Event", layout="wide", page_icon="🥐")

st.markdown("""
    <style>
    .stApp { background-color: #FDFBF7; }
    .stTextArea textarea { border: 2px solid #D7CCC8 !important; border-radius: 12px !important; }
    .stButton>button { 
        background: #5D4037; color: white !important; border-radius: 50px !important; 
        padding: 10px 25px !important; width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CLASSE PDF (NOUVEAU DESIGN) ---
class PDF(FPDF):
    def header(self):
        # Image de fond ou Logo (Optionnel si tu as le fichier)
        self.set_font('Arial', 'B', 24)
        self.set_text_color(139, 115, 85) # Couleur dorée/brune
        self.cell(0, 15, 'D E V I S', 0, 1, 'C')
        self.set_font('Arial', 'I', 12)
        self.cell(0, 5, 'Wassah Event', 0, 1, 'C')
        self.ln(10)

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    
    # --- Bloc Infos Client ---
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    
    # On affiche les infos client de manière simple
    for ligne in client_info:
        pdf.cell(0, 7, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    pdf.ln(15)
    
    # --- Section Prestations Incluses ---
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(93, 64, 55)
    pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=12)
    pdf.set_text_color(50, 50, 50)
    
    # Affichage sous forme de liste à puces comme sur ton image
    for _, row in df_panier.iterrows():
        designation = str(row['Désignation']).encode('latin-1', 'replace').decode('latin-1')
        # On enlève le [?] si présent pour le PDF final
        clean_name = designation.replace("[?] ", "")
        
        # Ligne de la prestation avec une puce
        pdf.cell(10) # Marge à gauche
        pdf.cell(0, 8, f"  -  {clean_name} (x{int(row['Qté'])})", 0, 1, 'L')

    pdf.ln(20)
    
    # --- Tarif Total ---
    pdf.set_font("Arial", 'I', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR  ", 0, 1, 'R')
    
    # --- Bas de page / Remerciements ---
    pdf.ln(30)
    pdf.set_font("Arial", 'I', 16)
    pdf.set_text_color(139, 115, 85)
    pdf.cell(0, 10, "MERCI DE VOTRE CONFIANCE", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. LOGIQUE D'ANALYSE ---
def analyser_texte(texte, df_catalogue):
    lignes = texte.split('\n')
    infos_client = []
    panier_detecte = []
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne: continue
        if "-" in ligne and any(char.isdigit() for char in ligne):
            # Extraction Qte et Nom
            match = re.search(r'(\d+)', ligne)
            qte = int(match.group(1)) if match else 1
            nom_saisi = re.sub(r'[-\d+]', '', ligne).strip().lower()
            
            produit_trouve = None
            prix = 0.0
            for _, row in df_catalogue.iterrows():
                if nom_saisi in str(row['Produit']).lower():
                    produit_trouve = row['Produit']
                    prix = float(row['Prix'])
                    break
            
            panier_detecte.append({
                "Désignation": produit_trouve if produit_trouve else f"[?] {nom_saisi}",
                "Prix Unit.": prix,
                "Qté": qte
            })
        else:
            infos_client.append(ligne)
    return infos_client, panier_detecte

# --- 4. INTERFACE ---
st.title("🥐 Devo : Événement Wassah")

try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("Catalogue introuvable")
    st.stop()

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

c1, c2 = st.columns(2)

with c1:
    st.subheader("1. La Demande")
    txt = st.text_area("Zone de texte :", height=250)
    if st.button("✨ Créer le Brouillon"):
        client, panier = analyser_texte(txt, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)

with c2:
    st.subheader("2. Le Devis Final")
    if not st.session_state['panier_df'].empty:
        # Édition des prix si nécessaire (car les [?] sont à 0€)
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True)
        
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
        
        st.download_button("📩 Télécharger le PDF", pdf_bytes, "devis_wassah.pdf", "application/pdf")
