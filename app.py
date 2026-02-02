import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import os

# --- 1. CONFIGURATION & BARRE LATÉRALE ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

st.sidebar.title("⚙️ Personnalisation")

# Personnalisation visuelle
uploaded_bg = st.sidebar.file_uploader("1. Changer le Fond (PNG/JPG)", type=["png", "jpg"])

# Infos de l'entreprise
nom_pro = st.sidebar.text_input("2. Nom de ton entreprise", "Wassah Event")
contact_pro = st.sidebar.text_input("3. Contact & Tel", "Ward - 06.65.62.00.92")
insta_pro = st.sidebar.text_input("4. Instagram", "@wassah.event")
lieu_pro = st.sidebar.text_input("5. Ta Ville/Département", "94")

# Gestion du Catalogue
st.sidebar.subheader("6. Tes Tarifs")
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

df_catalogue = st.sidebar.data_editor(df_catalogue, num_rows="dynamic", use_container_width=True)

# --- 2. LOGIQUE PDF AVEC LIEN AUTOMATIQUE AU FOND ---
class PDF(FPDF):
    def header(self):
        # LIEN AUTOMATIQUE : Priorité au fichier chargé, sinon utilise fond_devis.png
        if uploaded_bg:
            self.image(uploaded_bg, x=0, y=0, w=210, h=297)
        elif os.path.exists("fond_devis.png"):
            self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        
        # En-tête (Alignement basé sur ton modèle)
        self.set_y(55) 
        self.set_font('Arial', 'I', 10)
        self.set_text_color(139, 115, 85)
        self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')
        
        # Bloc Contact dynamique
        self.set_y(80); self.set_x(25) 
        self.set_font('Arial', '', 9); self.set_text_color(0, 0, 0)
        self.cell(0, 5, f"Contact : {contact_pro}", 0, 1, 'L')
        self.set_x(25); self.cell(0, 5, f"Insta : {insta_pro}", 0, 1, 'L')
        self.set_x(25); self.cell(0, 5, f"Lieu : {lieu_pro}", 0, 1, 'L')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    
    # Bloc Client (Haut Droite)
    pdf.set_y(80); pdf.set_font("Arial", 'B', 10); pdf.set_right_margin(25)
    pdf.cell(0, 5, f"Devis {nom_pro} pour :", 0, 1, 'R')
    pdf.set_font("Arial", size=10)
    for ligne in client_info:
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    # Prestations incluses
    pdf.set_y(135); pdf.set_font("Arial", 'B', 13); pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.set_font("Arial", size=11)
    for _, row in df_panier.iterrows():
        pdf.set_x(40)
        pdf.cell(0, 8, f"- {row['Désignation']} (x{int(row['Qté'])})", 0, 1, 'L')

    # Total Final
    pdf.set_y(220); pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'R')
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. LOGIQUE D'ANALYSE ---
def analyser_texte(texte, df_cat):
    lignes = texte.split('\n')
    client, panier = [], []
    for l in lignes:
        l = l.strip()
        if not l: continue
        match = re.search(r'(\d+)', l)
        if match and ("-" in l or any(p in l.lower() for p in ["box", "westaf", "brick", "pastel"])):
            qte = int(match.group(1))
            nom_saisi = re.sub(r'[-\d+]', '', l).strip().lower()
            nom_final, prix = nom_saisi, 0.0
            for _, row in df_cat.iterrows():
                if nom_saisi in str(row['Produit']).lower():
                    nom_final, prix = row['Produit'], float(row['Prix'])
                    break
            panier.append({"Désignation": nom_final, "Prix Unit.": prix, "Qté": qte})
        else: client.append(l)
    return client, panier

# --- 4. INTERFACE DE TRAVAIL ---
st.title(f"🥐 Devo : {nom_pro}")

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Message Client")
    txt = st.text_area("Colle la demande ici :", height=200, key="input_text")
    if st.button("✨ Analyser"):
        client, panier = analyser_texte(txt, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)
        st.rerun()

with col2:
    st.subheader("2. Finalisation (Modifie ici)")
    if not st.session_state['panier_df'].empty:
        # Modifie ici : les changements sont gardés en mémoire sans retaper le prompt
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        st.markdown(f"### Total : {total:.2f} €")
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
        st.download_button("📩 Télécharger le PDF", pdf_bytes, f"devis_{nom_pro}.pdf", "application/pdf", use_container_width=True)
    else:
        st.info("Colle une demande à gauche pour commencer.")
