import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import os

# --- 1. CONFIGURATION DE L'INTERFACE ---
st.set_page_config(page_title="Devo Pro - Wassah Event", layout="wide", page_icon="🥐")

# Barre latérale pour les réglages rapides
st.sidebar.title("🎨 Design du Devis")
uploaded_bg = st.sidebar.file_uploader("Changer l'image de fond", type=["png", "jpg", "jpeg"])
nom_pro = st.sidebar.text_input("Nom de l'entreprise", "Wassah Event")

# Chargement du catalogue pour l'ajout rapide
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# Système de sélection automatique vers le message
st.sidebar.subheader("🛒 Catalogue Produits")
selection = st.sidebar.dataframe(df_catalogue, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if 'produits_text' not in st.session_state: 
    st.session_state['produits_text'] = ""

if selection and selection['selection']['rows']:
    for idx in selection['selection']['rows']:
        p = df_catalogue.iloc[idx]['Produit']
        if p not in st.session_state['produits_text']:
            st.session_state['produits_text'] += f"- 1 {p}\n"

# --- 2. MOTEUR DE FUSION PDF ---
class PDF(FPDF):
    def header(self):
        # Fusion intelligente de l'image de fond
        try:
            if uploaded_bg:
                self.image(uploaded_bg, x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.jpg"):
                self.image("fond_devis.jpg", x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.png"):
                self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        except Exception:
            pass # Si aucune image, le PDF reste blanc mais fonctionnel
        
        # En-tête stylisé
        self.set_y(52)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(139, 115, 85) # Couleur dorée/marron comme ton logo
        self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')

    def footer(self):
        # Note esthétique en bas
        self.set_y(-25)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, "Devis généré numériquement par Wassah Event", 0, 0, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Bloc Client - Positionné pour éviter le logo haut-droite
    pdf.set_y(78)
    pdf.set_right_margin(22)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "DEVIS PRESTATION", 0, 1, 'R')
    
    pdf.set_font("Helvetica", size=10)
    txt_client = client_info if client_info else "Informations Client"
    for ligne in txt_client.split('\n'):
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    # 2. Tableau des prestations - Centré esthétiquement
    pdf.set_y(130)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(93, 64, 55)
    pdf.cell(0, 10, "Détail des Prestations", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(50, 50, 50)
    for _, row in df_panier.iterrows():
        pdf.set_x(35) # Marge gauche pour l'esthétique
        item = f"- {row['Désignation']} (x{int(row['Qté'])})"
        pdf.cell(0, 8, txt=item.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='L')

    # 3. Bloc Total - Mis en valeur en bas
    pdf.set_y(225)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"TOTAL TTC : {total_ttc:.2f} EUR  ", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. INTERFACE UTILISATEUR EN 3 COLONNES ---
st.title(f"🥐 Devo : {nom_pro}")

if 'panier_df' not in st.session_state: 
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])

c1, c2, c3 = st.columns([1, 1, 1.2]) # Ajustement des largeurs pour plus de confort

with c1:
    st.subheader("👤 Infos Client")
    client_txt = st.text_area("Coordonnées...", height=180, placeholder="Nom du client\nDate de l'événement\nLieu de prestation")

with c2:
    st.subheader("📝 Commande")
    prod_txt = st.text_area("Sélection produits :", value=st.session_state['produits_text'], height=180)
    st.session_state['produits_text'] = prod_txt
    if st.button("✨ Analyser la commande", use_container_width=True):
        lignes = prod_txt.split('\n')
        panier = []
        for l in lignes:
            match = re.search(r'(\d+)', l)
            if match:
                qte = int(match.group(1))
                nom = re.sub(r'[-\d+]', '', l).strip()
                prix = 0.0
                for _, row in df_catalogue.iterrows():
                    if nom.lower() in str(row['Produit']).lower():
                        prix, nom = float(row['Prix']), row['Produit']; break
                panier.append({"Désignation": nom, "Prix Unit.": prix, "Qté": qte})
        st.session_state['panier_df'] = pd.DataFrame(panier)
        st.rerun()

with c3:
    st.subheader("📊 Devis Final")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        st.info(f"Montant Total : **{total:.2f} €**")
        
        pdf_bytes = generer_pdf(client_txt, edited_df, total)
        st.download_button("📩 Télécharger mon Devis Design", pdf_bytes, "devis_wassah.pdf", "application/pdf", use_container_width=True)
    else:
        st.warning("Coche des produits dans le catalogue à gauche 👈")
