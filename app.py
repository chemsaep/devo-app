import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import os

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# --- BARRE LATÉRALE ---
st.sidebar.title("⚙️ Personnalisation")
uploaded_bg = st.sidebar.file_uploader("Changer le Fond", type=["png", "jpg", "jpeg"])
nom_pro = st.sidebar.text_input("Nom entreprise", "Wassah Event")
contact_pro = st.sidebar.text_input("Contact", "06.65.62.00.92")

# CATALOGUE
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

selection = st.sidebar.dataframe(df_catalogue, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if 'produits_text' not in st.session_state: st.session_state['produits_text'] = ""

if selection and selection['selection']['rows']:
    for idx in selection['selection']['rows']:
        p = df_catalogue.iloc[idx]['Produit']
        if p not in st.session_state['produits_text']:
            st.session_state['produits_text'] += f"- 1 {p}\n"

# --- 2. LOGIQUE DE FUSION IMAGE & TEXTE ---
class PDF(FPDF):
    def header(self):
        # CONDITION DE FUSION : On teste les fichiers existants sur GitHub
        try:
            if uploaded_bg:
                self.image(uploaded_bg, x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.jpg"):
                self.image("fond_devis.jpg", x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.png"):
                self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        except Exception:
            pass # Continue sans image si aucun fichier n'est trouvé
        
        # Superposition du texte sur l'image
        self.set_y(55)
        self.set_font('Arial', 'I', 10)
        self.set_text_color(139, 115, 85)
        self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page() # C'est ici que l'image et le texte fusionnent
    
    # Positionnement des blocs sur le fond
    pdf.set_y(80)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_right_margin(25)
    pdf.cell(0, 5, f"Devis {nom_pro} pour :", 0, 1, 'R')
    
    pdf.set_font("Arial", size=10)
    txt_client = client_info if client_info else "Client"
    for ligne in txt_client.split('\n'):
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    # Zone des prestations
    pdf.set_y(135)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(50, 50, 50)
    for _, row in df_panier.iterrows():
        pdf.set_x(40)
        pdf.cell(0, 8, f"- {row['Désignation']} (x{int(row['Qté'])})", 0, 1, 'L')

    # Montant total
    pdf.set_y(220)
    pdf.set_font("Arial", 'B', 13)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. INTERFACE UTILISATEUR ---
st.title(f"🥐 Devo : {nom_pro}")
if 'panier_df' not in st.session_state: 
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("1. Infos Client")
    client_txt = st.text_area("Coordonnées...", height=150)

with col2:
    st.subheader("2. Commande")
    prod_txt = st.text_area("Produits :", value=st.session_state['produits_text'], height=150)
    st.session_state['produits_text'] = prod_txt
    if st.button("✨ Analyser"):
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

with col3:
    st.subheader("3. Résultat")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        st.markdown(f"### Total : {total:.2f} €")
        
        pdf_bytes = generer_pdf(client_txt, edited_df, total)
        st.download_button("📩 Télécharger le PDF", pdf_bytes, "devis.pdf", "application/pdf", use_container_width=True)
