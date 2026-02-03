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

# --- CATALOGUE AVEC SÉLECTION (CLIC AUTOMATIQUE) ---
st.sidebar.subheader("6. Tes Tarifs")
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# Affichage du catalogue avec cases à cocher
selection = st.sidebar.dataframe(
    df_catalogue, 
    use_container_width=True, 
    hide_index=True, 
    on_select="rerun", 
    selection_mode="multi-row"
)

# Mémoire du texte pour les produits
if 'produits_text' not in st.session_state:
    st.session_state['produits_text'] = ""

# Si on coche dans le catalogue, on ajoute au texte
if selection and selection['selection']['rows']:
    lignes = ""
    for idx in selection['selection']['rows']:
        p = df_catalogue.iloc[idx]['Produit']
        if p not in st.session_state['produits_text']:
            lignes += f"- 1 {p}\n"
    st.session_state['produits_text'] += lignes

# --- 2. LOGIQUE PDF ---
class PDF(FPDF):
    def header(self):
        try:
            if uploaded_bg:
                self.image(uploaded_bg, x=0, y=0, w=210, h=297)
            elif os.path.exists("fond_devis.png"):
                self.image("fond_devis.png", x=0, y=0, w=210, h=297)
        except:
            pass
        
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
    for ligne in client_info.split('\n'):
        pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    pdf.set_y(135); pdf.set_font("Arial", 'B', 13); pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.set_font("Arial", size=11)
    for _, row in df_panier.iterrows():
        pdf.set_x(40)
        pdf.cell(0, 8, f"- {row['Désignation']} (x{int(row['Qté'])})", 0, 1, 'L')

    pdf.set_y(220); pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'R')
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. INTERFACE PRINCIPALE ---
st.title(f"🥐 Devo : {nom_pro}")

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])

# Création des 3 colonnes
col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Infos Client")
    client_txt = st.text_area("Nom, Date, Adresse...", height=150, placeholder="Moussa Diop\n11/08/2026\nLieu : 94")

with col2:
    st.subheader("2. Message / Produits")
    prod_txt = st.text_area("Détails de la commande :", value=st.session_state['produits_text'], height=150)
    st.session_state['produits_text'] = prod_txt # Garde les modifs manuelles
    
    if st.button("✨ Analyser la commande"):
        # Analyse des produits uniquement
        lignes = prod_txt.split('\n')
        panier = []
        for l in lignes:
            l = l.strip()
            if not l: continue
            match = re.search(r'(\d+)', l)
            if match:
                qte = int(match.group(1))
                nom = re.sub(r'[-\d+]', '', l).strip()
                prix = 0.0
                for _, row in df_catalogue.iterrows():
                    if nom.lower() in str(row['Produit']).lower():
                        prix, nom = float(row['Prix']), row['Produit']
                        break
                panier.append({"Désignation": nom, "Prix Unit.": prix, "Qté": qte})
        st.session_state['panier_df'] = pd.DataFrame(panier)
        st.rerun()

with col3:
    st.subheader("3. Finalisation")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        st.markdown(f"### Total : {total:.2f} €")
        
        pdf_bytes = generer_pdf(client_txt, edited_df, total)
        st.download_button("📩 Télécharger le PDF", pdf_bytes, f"devis_{nom_pro}.pdf", "application/pdf")
    else:
        st.info("Coche des tarifs ou écris à gauche.")
