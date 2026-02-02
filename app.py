import streamlit as st
import pandas as pd
import re
from fpdf import FPDF

# --- 1. CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# --- 2. BARRE LATÉRALE DE PERSONNALISATION ---
st.sidebar.title("⚙️ Personnalisation")

# Choix du fond
uploaded_bg = st.sidebar.file_uploader("1. Ton Fond de Devis (PNG/JPG)", type=["png", "jpg"])
fond_final = uploaded_bg if uploaded_bg else "fond_devis.png"

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

# Modification des tarifs en direct
df_catalogue = st.sidebar.data_editor(df_catalogue, num_rows="dynamic", use_container_width=True)

# --- 3. LOGIQUE PDF ---
class PDF(FPDF):
    def header(self):
        try:
            self.image(fond_final, x=0, y=0, w=210, h=297)
        except:
            pass
        
        # En-tête
        self.set_y(55) 
        self.set_font('Arial', 'I', 10)
        self.set_text_color(139, 115, 85)
        self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')
        
        # Bloc Contact
        self.set_y(80)
        self.set_x(25) 
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        self.cell(0, 5, f"Contact : {contact_pro}", 0, 1, 'L')
        self.set_x(25)
        self.cell(0, 5, f"Insta : {insta_pro}", 0, 1, 'L')
        self.set_x(25)
        self.cell(0, 5, f"Lieu : {lieu_pro}", 0, 1, 'L')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    
    # Bloc Client (Haut Droite)
    pdf.set_y(80)
    pdf.set_font("Arial", 'B', 10)
    pdf.set_right_margin(25)
    pdf.cell(0, 5, f"Devis {nom_pro} pour :", 0, 1, 'R')
    pdf.set_font("Arial", size=10)
    for ligne in client_info:
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    # Prestations
    pdf.set_y(135) 
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.set_font("Arial", size=11)
    for _, row in df_panier.iterrows():
        pdf.set_x(40)
        pdf.cell(0, 8, f"- {row['Désignation']} (x{int(row['Qté'])})", 0, 1, 'L')

    # Total
    pdf.set_y(220)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. ANALYSE DU TEXTE ---
def analyser_texte(texte, df_cat):
    lignes = texte.split('\n')
    client, panier = [], []
    for l in lignes:
        l = l.strip()
        if not l: continue
        match = re.search(r'(\d+)', l)
        if match and ("-" in l or any(p in l.lower() for p in ["box", "westaf", "brick", "pastel", "coffret"])):
            qte = int(match.group(1))
            nom_saisi = re.sub(r'[-\d+]', '', l).strip().lower()
            nom_final, prix = nom_saisi, 0.0
            for _, row in df_cat.iterrows():
                if nom_saisi in str(row['Produit']).lower():
                    nom_final, prix = row['Produit'], float(row['Prix'])
                    break
            panier.append({"Désignation": nom_final, "Prix Unit.": prix, "Qté": qte})
        else:
            client.append(l)
    return client, panier

# --- 5. INTERFACE DE TRAVAIL ---
st.title(f"🥐 Devo : {nom_pro}")

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Message Client")
    txt = st.text_area("Colle la demande ici :", height=200)
    if st.button("✨ Analyser"):
        client, panier = analyser_texte(txt, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)
        st.rerun()

with col2:
    st.subheader("2. Finalisation")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        st.markdown(f"### Total : {total:.2f} €")
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
        st.download_button("📩 Télécharger le PDF", pdf_bytes, "devis.pdf", "application/pdf")
