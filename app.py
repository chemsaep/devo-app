import streamlit as st
import pandas as pd
from fpdf import FPDF
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo", layout="wide", page_icon="🥐")

# --- 2. CLASSE PDF PERSONNALISÉE ---
class PDF(FPDF):
    def header(self):
        # Arrière-plan complet
        try:
            self.image('fond_devis.png', x=0, y=0, w=210, h=297)
        except:
            pass
        
        # Texte d'en-tête (Sous le logo)
        self.set_y(50)
        self.set_font('Arial', 'I', 11)
        self.set_text_color(139, 115, 85)
        self.cell(0, 10, "Des événements sur-mesure pour toutes vos occasions", 0, 1, 'C')
        
        # Bloc Contact (Gauche)
        self.set_y(70)
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        self.cell(0, 6, "Contact : [Ward] - 06.65.62.00.92", 0, 1, 'L')
        self.cell(0, 6, "Insta : @wassah.event", 0, 1, 'L')
        self.cell(0, 6, "Lieu : 94", 0, 1, 'L')

    def footer(self):
        # Conditions et Remerciements en bas
        self.set_y(-50)
        self.set_font('Arial', '', 8)
        self.set_text_color(50, 50, 50)
        cond1 = "Conditions - Paiement possible en 2 fois (Acompte de 50% à payer lors de la réservation)"
        cond2 = "Aucun remboursement en cas d'annulation moins de 7 jours avant"
        self.cell(0, 4, cond1.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
        self.cell(0, 4, cond2.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
        
        self.ln(10)
        self.set_font('Arial', 'I', 16)
        self.set_text_color(139, 115, 85)
        self.cell(0, 10, "MERCI DE VOTRE CONFIANCE", 0, 1, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Bloc Client (Droite)
    pdf.set_y(70)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, "Devis prestation déco :", 0, 1, 'R')
    pdf.set_font("Arial", size=10)
    
    # On extrait intelligemment le nom, la date et le lieu du texte client
    for ligne in client_info:
        pdf.cell(0, 6, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
    
    # 2. Section Prestations
    pdf.set_y(135) # Positionnement central
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(93, 64, 55)
    pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.set_text_color(0, 0, 0)
    for _, row in df_panier.iterrows():
        nom = str(row['Désignation']).replace("[?] ", "").encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(30) # Marge gauche
        pdf.cell(0, 8, f"  -  {nom} (x{int(row['Qté'])})", 0, 1, 'L')

    # 3. Tarif Total
    pdf.set_y(210)
    pdf.set_font("Arial", 'B', 13)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR  ", 0, 1, 'R')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 3. LOGIQUE D'ANALYSE ---
def analyser_texte(texte, df_catalogue):
    lignes = texte.split('\n')
    infos_client = []
    panier_detecte = []
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne: continue
        if "-" in ligne or any(p in ligne.lower() for p in ["box", "westaf", "brick", "pastel"]):
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

# --- 4. INTERFACE ---
st.title("🥐 Devo : Wassah Event")

try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("Catalogue.csv introuvable")
    st.stop()

if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. La Demande")
    txt = st.text_area("Entrez les détails ici :", height=250, placeholder="Moussa Diop\nDate : 11/08/2026\nLieu : 94\n- 1 Westaf 100")
    if st.button("✨ Créer le Devis"):
        client, panier = analyser_texte(txt, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)

with col2:
    st.subheader("2. Le Devis Final")
    if not st.session_state['panier_df'].empty:
        edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True)
        total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
        
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
        st.download_button("📩 Télécharger le PDF", pdf_bytes, "devis_wassah.pdf", "application/pdf")
