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
nom_pro = st.sidebar.text_input("2. Nom entreprise", "Wassah Event")
contact_pro = st.sidebar.text_input("3. Contact & Tel", "Ward - 06.65.62.00.92")
insta_pro = st.sidebar.text_input("4. Instagram", "@wassah.event")
lieu_pro = st.sidebar.text_input("5. Ta Ville/Département", "94")

# --- 6. GESTION DU CATALOGUE (FONCTION CLIC) ---
st.sidebar.subheader("6. Tes Tarifs")
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# On affiche le catalogue avec sélection possible
selection = st.sidebar.dataframe(
    df_catalogue, 
    use_container_width=True, 
    hide_index=True, 
    on_select="rerun", 
    selection_mode="multi-row"
)

# Récupération des lignes cochées pour les ajouter au prompt
if 'input_text' not in st.session_state:
    st.session_state['input_text'] = ""

if selection and selection['selection']['rows']:
    lignes_ajoutees = ""
    for idx in selection['selection']['rows']:
        produit = df_catalogue.iloc[idx]['Produit']
        lignes_ajoutees += f"- 1 {produit}\n"
    
    # On ajoute au texte existant si ce n'est pas déjà dedans
    if lignes_ajoutees not in st.session_state['input_text']:
        st.session_state['input_text'] += lignes_ajoutees

# --- 2. LOGIQUE PDF CORRIGÉE ---
class PDF(FPDF):
    def header(self):
        # Correction du bug AttributeError : on vérifie que l'image existe
        try:
            if uploaded_bg:
                self.image(uploaded_bg, x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.png"):
                self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        except:
            pass # Si l'image est corrompue ou absente, on continue sans fond
        
        self.set_y(55); self.set_font('Arial', 'I', 10); self.set_text_color(139, 115, 85)
        self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')
        
        self.set_y(80); self.set_x(25); self.set_font('Arial', '', 9); self.set_text_color(0, 0, 0)
        self.cell(0, 5, f"Contact : {contact_pro}", 0, 1, 'L')
        self.set_x(25); self.cell(0, 5, f"Insta : {insta_pro}", 0, 1, 'L')
        self.set_x(25); self.cell(0, 5, f"Lieu : {lieu_pro}", 0, 1, 'L')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    pdf.set_y(80); pdf.set_font("Arial", 'B', 10); pdf.set_right_margin(25)
    pdf.cell(0, 5, f"Devis {nom_pro} pour :", 0, 1, 'R')
    pdf.set_font("Arial", size=10)
    for ligne in client_info:
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    pdf.set_y(135); pdf.set_font("Arial", 'B', 13); pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.set_font("Arial", size=11)
    for _, row in df_panier.iterrows():
        pdf.set_x(40)
        pdf.cell(0, 8, f"- {row['Désignation']} (x{int(row['Qté'])})", 0, 1, 'L')

    pdf.set_y(220); pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'R')
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. INTERFACE DE TRAVAIL ---
st.title(f"🥐 Devo : {nom_pro}")

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Message Client")
    # Le texte est maintenant lié à la session_state pour recevoir les clics du catalogue
    txt = st.text_area("Colle la demande ici :", value=st.session_state['input_text'], height=250)
    
    # Mise à jour manuelle si on écrit dedans
    st.session_state['input_text'] = txt

    if st.button("✨ Analyser et Créer le Devis"):
        # Importation de la fonction d'analyse simplifiée
        lignes = txt.split('\n')
        client, panier = [], []
        for l in lignes:
            l = l.strip()
            if not l: continue
            match = re.search(r'(\d+)', l)
            if match:
                qte = int(match.group(1))
                nom = re.sub(r'[-\d+]', '', l).strip()
                # On cherche le prix dans le catalogue
                prix = 0.0
                for _, row in df_catalogue.iterrows():
                    if nom.lower() in str(row['Produit']).lower():
                        prix = float(row['Prix'])
                        nom = row['Produit']
                        break
                panier.append({"Désignation": nom, "Prix Unit.": prix, "Qté": qte})
            else:
                client.append(l)
        
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)
        st.rerun()

with col2:
    st.subheader("2. Finalisation")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        st.markdown(f"### Total : {total:.2f} €")
        
        try:
            pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
            st.download_button("📩 Télécharger le PDF", pdf_bytes, f"devis_{nom_pro}.pdf", "application/pdf")
        except Exception as e:
            st.error(f"Erreur lors de la génération du PDF : {e}")
