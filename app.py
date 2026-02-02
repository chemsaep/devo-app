import streamlit as st
import pandas as pd
from fpdf import FPDF
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo", layout="wide", page_icon="🥐")

# --- 2. CLASSE PDF AVEC FOND ---
class PDF(FPDF):
    def header(self):
        # Image d'arrière-plan couvrant toute la page A4
        try:
            # Utilise le nom exact du fichier présent sur ton GitHub
            self.image('fond_devis.png', x=0, y=0, w=210, h=297)
        except:
            st.error("L'image 'fond_devis.png' est introuvable dans le dossier.")

    def footer(self):
        # Positionnement du message de fin en bas
        self.set_y(-40)
        self.set_font('Arial', 'I', 16)
        self.set_text_color(139, 115, 85)
        self.cell(0, 10, "MERCI DE VOTRE CONFIANCE", 0, 1, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Infos Client (Alignées en haut à droite)
    pdf.set_y(65) # Ajusté pour laisser passer l'en-tête de ton image
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    for ligne in client_info:
        line_clean = str(ligne).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 7, txt=line_clean, ln=True, align='R')
    
    pdf.ln(20)
    
    # 2. Titre Prestations (Centré)
    pdf.set_font("Arial", 'B', 16)
    pdf.set_text_color(93, 64, 55)
    pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.ln(5)
    
    # 3. Liste à puces (Simple et aérée)
    pdf.set_font("Arial", size=13)
    pdf.set_text_color(50, 50, 50)
    for _, row in df_panier.iterrows():
        designation = str(row['Désignation']).replace("[?] ", "")
        nom_clean = designation.encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(25) # Marge gauche pour centrer la liste
        pdf.cell(0, 10, f"- {nom_clean} (x{int(row['Qté'])})", 0, 1, 'L')

    pdf.ln(15)
    
    # 4. Tarif Total (Aligné à droite)
    pdf.set_font("Arial", 'B', 15)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR  ", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. ANALYSE DU TEXTE ---
def analyser_texte(texte, df_catalogue):
    lignes = texte.split('\n')
    infos_client = []
    panier_detecte = []
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne: continue
        # Détection des produits via tiret ou mots clés
        if "-" in ligne or any(p in ligne.lower() for p in ["box", "westaf", "light", "mid"]):
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
                "Prix Unit.": prix, "Qté": qte
            })
        else:
            infos_client.append(ligne)
    return infos_client, panier_detecte

# --- 4. INTERFACE STREAMLIT ---
st.title("🥐 Devo : Wassah Event")

try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("Fichier catalogue.csv manquant.")
    st.stop()

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Demande")
    txt = st.text_area("Colle la demande ici (ex: Moussa Diop - 2 box) :", height=250)
    if st.button("✨ Analyser la commande"):
        client, panier = analyser_texte(txt, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)

with col2:
    st.subheader("2. Finalisation")
    if not st.session_state['panier_df'].empty:
        # Tableau éditable pour ajuster les prix ou noms
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True)
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        
        st.markdown(f"### Total : {total:.2f} €")
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
        st.download_button("📩 Télécharger le Devis Officiel", pdf_bytes, "devis_wassah.pdf", "application/pdf")
