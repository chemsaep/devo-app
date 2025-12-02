import streamlit as st
import pandas as pd
from fpdf import FPDF
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Devo - Wassah Event", layout="wide", page_icon="🥐")

# --- 2. CSS (DESIGN) ---
st.markdown("""
    <style>
    .stApp { background-color: #F7F3E8; color: #4E342E; }
    h1, h2, h3 { color: #5D4037 !important; }
    .stTextArea textarea { background-color: #FFFFFF; color: #4E342E; border: 1px solid #D7CCC8; }
    .stButton>button { background-color: #D7CCC8; color: #3E2723; border-radius: 8px; border: none; font-weight: bold; width: 100%; }
    .stButton>button:hover { background-color: #BCAAA4; color: white; }
    div[data-testid="stDataFrame"] { background-color: white; padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. FONCTION PDF (LE COEUR DU MODÈLE) ---
class PDF(FPDF):
    def header(self):
        # Fond Beige sur toute la page (optionnel, sinon juste blanc)
        # self.set_fill_color(247, 243, 232)
        # self.rect(0, 0, 210, 297, 'F')
        
        # Titre Principal
        self.set_font('Arial', 'B', 24)
        self.set_text_color(93, 64, 55) # Marron Chocolat
        self.cell(0, 10, 'DEVIS', 0, 1, 'C')
        
        # Nom de l'entreprise
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Wassah Event', 0, 1, 'C')
        
        # Slogan
        self.set_font('Arial', 'I', 10)
        self.cell(0, 5, 'Des événements sur-mesure pour toutes vos occasions', 0, 1, 'C')
        self.ln(2)
        
        # Bloc Contact (Encadré ou centré)
        self.set_font('Arial', '', 9)
        self.set_text_color(0, 0, 0)
        contact_text = "Contact: Waré 06.65.62.00.92  |  Insta: @wassah.event  |  Lieu: 94"
        self.cell(0, 5, contact_text, 0, 1, 'C')
        self.ln(5)
        
        # Ligne de séparation
        self.set_draw_color(93, 64, 55)
        self.line(10, 45, 200, 45)
        self.ln(10)

    def footer(self):
        self.set_y(-30)
        self.set_font('Arial', 'B', 12)
        self.set_text_color(93, 64, 55)
        self.cell(0, 10, 'MERCI DE VOTRE CONFIANCE', 0, 1, 'C')
        
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generer_pdf(client_info, df_panier, total_ttc):
    pdf = PDF()
    pdf.add_page()
    pdf.set_text_color(0, 0, 0)
    
    # --- BLOC CLIENT ---
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Devis prestation :", ln=True)
    
    pdf.set_font("Arial", '', 11)
    # Fond beige pour le bloc client
    pdf.set_fill_color(253, 248, 240) 
    
    # On construit une boite multi-lignes pour les infos client
    infos_str = ""
    for ligne in client_info:
        infos_str += ligne + "\n"
    
    # On nettoie les caractères spéciaux
    infos_str = infos_str.encode('latin-1', 'replace').decode('latin-1')
    
    pdf.multi_cell(0, 6, infos_str, fill=True, border=0)
    pdf.ln(8)
    
    # --- TABLEAU DES PRESTATIONS ---
    pdf.set_font("Arial", 'B', 12)
    pdf.set_fill_color(230, 218, 208) # Marron clair pour l'en-tête
    pdf.cell(100, 10, "Prestations incluses", 1, 0, 'L', True)
    pdf.cell(30, 10, "Prix Unit.", 1, 0, 'C', True)
    pdf.cell(20, 10, "Qté", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    pdf.set_font("Arial", size=11)
    # On itère sur le DataFrame final
    for index, row in df_panier.iterrows():
        nom = str(row['Désignation']).encode('latin-1', 'replace').decode('latin-1')
        prix = float(row['Prix Unit.'])
        qte = int(row['Qté'])
        total_ligne = float(row['Total'])
        
        pdf.cell(100, 10, nom, 1)
        pdf.cell(30, 10, f"{prix:.2f}", 1, 0, 'R')
        pdf.cell(20, 10, str(qte), 1, 0, 'C')
        pdf.cell(40, 10, f"{total_ligne:.2f}", 1, 1, 'R')
    
    pdf.ln(5)
    
    # --- TOTAL ---
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(150, 10, "Tarif total :", 0, 0, 'R')
    pdf.cell(40, 10, f"{total_ttc:.2f} EUR", 1, 1, 'R')
    pdf.ln(10)
    
    # --- CONDITIONS (Copie exacte du PDF) ---
    pdf.set_font("Arial", 'U', 10) # Souligné
    pdf.cell(0, 6, "Conditions :", ln=True)
    
    pdf.set_font("Arial", '', 9) # Normal
    pdf.cell(0, 5, "- Paiement possible en 2 fois (Acompte de 50% à payer lors de la réservation)", ln=True)
    pdf.cell(0, 5, "- Aucun remboursement en cas d'annulation moins de 7 jours avant", ln=True)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. ANALYSE (MOTEUR INTELLIGENT) ---
def analyser_texte(texte, df_catalogue):
    lignes = texte.split('\n')
    infos_client = []
    panier_detecte = []
    
    for ligne in lignes:
        ligne = ligne.strip()
        if not ligne: continue
        
        # Détection commande (si commence par tiret)
        if ligne.startswith("-"):
            commande_brute = ligne.replace("-", "").strip()
            match_qte = re.match(r"(\d+)\s*(.*)", commande_brute)
            if match_qte:
                qte = int(match_qte.group(1))
                txt_produit = match_qte.group(2).lower()
                
                produit_trouve = None
                prix_trouve = 0.0
                
                for index, row in df_catalogue.iterrows():
                    nom_catalogue = str(row['Produit'])
                    # Recherche partielle intelligente
                    if txt_produit in nom_catalogue.lower():
                        produit_trouve = nom_catalogue
                        prix_trouve = float(row['Prix'])
                        break
                
                if produit_trouve:
                    panier_detecte.append({"Désignation": produit_trouve, "Prix Unit.": prix_trouve, "Qté": qte})
                else:
                    panier_detecte.append({"Désignation": f"[?] {txt_produit}", "Prix Unit.": 0.0, "Qté": qte})
        else:
            # C'est une info client
            infos_client.append(ligne)
            
    return infos_client, panier_detecte

# --- 5. INTERFACE UTILISATEUR ---
st.title("🥐 Devo : Wassah Event")

# Chargement catalogue
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    st.error("⚠️ Fichier catalogue.csv introuvable.")
    st.stop()

# Initialisation Session
if 'panier_df' not in st.session_state:
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
if 'client_info' not in st.session_state:
    st.session_state['client_info'] = []

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. La Demande")
    st.info("Copie-colle les infos comme dans l'exemple ci-dessous :")
    
    # Exemple formaté comme le PDF
    exemple = """Client : Moussa Diop
Date : 08/11/2025
Lieu : 94
Thème : Princesse Rose

- 2 box gourmande
- 1 westaf 100"""
    
    texte_input = st.text_area("Zone de texte :", height=250, placeholder=exemple)
    
    if st.button("✨ Créer le Brouillon"):
        client, panier = analyser_texte(texte_input, df_catalogue)
        st.session_state['client_info'] = client
        st.session_state['panier_df'] = pd.DataFrame(panier)

with col2:
    st.subheader("2. Le Devis Final")
    
    if not st.session_state['panier_df'].empty:
        # Aperçu Client
        st.markdown(f"**Client :** {st.session_state['client_info'][0] if st.session_state['client_info'] else '...'}")
        
        # Tableau Éditable
        edited_df = st.data_editor(
            st.session_state['panier_df'],
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Prix Unit.": st.column_config.NumberColumn(format="%.2f €"),
                "Qté": st.column_config.NumberColumn(format="%d"),
            }
        )
        
        # Calcul Total
        edited_df["Total"] = edited_df["Prix Unit."] * edited_df["Qté"]
        grand_total = edited_df["Total"].sum()
        
        st.markdown("---")
        # Affichage Total Style Wassah
        st.markdown(f"<h3 style='text-align: right; color: #5D4037;'>Total : {grand_total:.2f} €</h3>", unsafe_allow_html=True)
        
        # Bouton PDF
        pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, grand_total)
        
        st.download_button(
            label="📄 Télécharger le Devis PDF (Wassah Style)",
            data=pdf_bytes,
            file_name="devis_wassah_event.pdf",
            mime="application/pdf",
            type="primary"
        )
    else:
        st.markdown("Remplis la zone de gauche pour commencer.")
