import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import os

# --- CONFIGURATION INTERFACE ---
st.set_page_config(page_title="Devo Pro - Fusion IA", layout="wide", page_icon="🥐")

# --- DESIGN & FOND ---
st.sidebar.title("🎨 Design Intelligent")
uploaded_bg = st.sidebar.file_uploader("Modifier le fond", type=["png", "jpg", "jpeg"])

# --- CATALOGUE DYNAMIQUE ---
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# Sélection intelligente vers le message
st.sidebar.subheader("🛒 Vos Produits")
selection = st.sidebar.dataframe(df_catalogue, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if 'produits_text' not in st.session_state: st.session_state['produits_text'] = ""

if selection and selection['selection']['rows']:
    for idx in selection['selection']['rows']:
        p = df_catalogue.iloc[idx]['Produit']
        if p not in st.session_state['produits_text']:
            st.session_state['produits_text'] += f"- 1 {p}\n"

# --- IA DE RENDU GRAPHIQUE (Moteur PDF) ---
class DesignIA(FPDF):
    def header(self):
        # Fusion automatique avec détection de format
        try:
            if uploaded_bg:
                self.image(uploaded_bg, x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.jpg"):
                self.image("fond_devis.jpg", x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.png"):
                self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        except:
            pass
        
        # En-tête avec typographie "Gold & Black"
        self.set_y(52)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(139, 115, 85) # Couleur or pour l'élégance
        self.cell(0, 10, "Des événements sur-mesure - Wassah Event", 0, 1, 'C')

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(180, 180, 180)
        self.cell(0, 10, "Document généré par l'IA Devo Pro - Wassah Event", 0, 0, 'C')

def fusionner_donnees_design(info_client, df_panier, total):
    pdf = DesignIA()
    pdf.add_page()
    
    # Positionnement IA : Bloc Client
    pdf.set_y(78)
    pdf.set_right_margin(22)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 6, "DEVIS PRESTATION", 0, 1, 'R')
    
    pdf.set_font("Helvetica", size=10)
    for ligne in info_client.split('\n'):
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    # Positionnement IA : Tableau des prestations
    pdf.set_y(130)
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(93, 64, 55) # Marron profond
    pdf.cell(0, 10, "Détail des Prestations", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(60, 60, 60)
    for _, row in df_panier.iterrows():
        pdf.set_x(35)
        item = f"- {row['Désignation']} (x{int(row['Qté'])})"
        pdf.cell(0, 8, txt=item.encode('latin-1', 'replace').decode('latin-1'), ln=True, align='L')

    # Bloc de Finition : Total
    pdf.set_y(225)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"TOTAL TTC : {total:.2f} EUR  ", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFACE UTILISATEUR (3 COLONNES) ---
st.title("🥐 Devo : Wassah Event")

if 'panier_df' not in st.session_state: 
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])

c1, c2, c3 = st.columns([1, 1, 1.2])

with c1:
    st.subheader("👤 Client")
    client_txt = st.text_area("Coordonnées...", height=180, placeholder="Nom\nDate\nAdresse")

with c2:
    st.subheader("📝 Commande")
    prod_txt = st.text_area("Produits :", value=st.session_state['produits_text'], height=180)
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
        ed_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        tot = (ed_df["Prix Unit."] * ed_df["Qté"]).sum()
        st.info(f"Montant Total : **{tot:.2f} €**")
        
        pdf_bytes = fusionner_donnees_design(client_txt, ed_df, tot)
        st.download_button("📩 Télécharger le PDF Fusionné", pdf_bytes, "devis_wassah.pdf", "application/pdf", use_container_width=True)
