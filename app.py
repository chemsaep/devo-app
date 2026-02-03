import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import tempfile
import os

# --- 1. CONFIGURATION DU MOTEUR ---
st.set_page_config(page_title="Devo Pro - IA Fusion", layout="wide", page_icon="🥐")

# --- 2. BARRE LATÉRALE : RÉGLAGES DESIGN ---
st.sidebar.title("🎨 IA de Mise en Page")
uploaded_bg = st.sidebar.file_uploader("Image de fond personnalisée", type=["png", "jpg", "jpeg"])

# Chargement du catalogue
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# Sélection rapide
st.sidebar.subheader("🛒 Produits Disponibles")
selection = st.sidebar.dataframe(df_catalogue, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if 'produits_text' not in st.session_state: 
    st.session_state['produits_text'] = ""

if selection and selection['selection']['rows']:
    for idx in selection['selection']['rows']:
        p = df_catalogue.iloc[idx]['Produit']
        if p not in st.session_state['produits_text']:
            st.session_state['produits_text'] += f"- 1 {p}\n"

# --- 3. L'IA DE FUSION (MOTEUR GRAPHIQUE AVEC TRANSPARENCE) ---
class FusionIA(FPDF):
    def __init__(self, bg_path=None):
        super().__init__()
        self.bg_path = bg_path
        self.ext_gstates = [] # Nécessaire pour gérer la transparence

    # --- FONCTIONS TECHNIQUES POUR LA TRANSPARENCE (ALPHA) ---
    def set_alpha(self, alpha, bm='Normal'):
        # Cette fonction active la transparence
        # alpha : 0.0 (invisible) à 1.0 (opaque)
        gs = {'ca': alpha, 'CA': alpha, 'BM': '/' + bm}
        self.ext_gstates.append(gs)
        self.set_ext_gstate(len(self.ext_gstates))

    def set_ext_gstate(self, n):
        self._out(f'/GS{n} gs')

    def _putextgstates(self):
        for i, gs in enumerate(self.ext_gstates):
            self._newobj()
            self._out('<</Type /ExtGState')
            for k, v in gs.items():
                self._out(f'/{k} {v}')
            self._out('>>')
            self._out('endobj')

    def _putresources(self):
        self._putextgstates()
        super()._putresources()
        if self.ext_gstates:
            self._out('/ExtGState <<')
            for i in range(1, len(self.ext_gstates) + 1):
                self._out(f'/GS{i} {self.n - len(self.ext_gstates) + i - 1} 0 R')
            self._out('>>')
    # ---------------------------------------------------------

    def header(self):
        # 1. FOND : Image Pleine Page (Toujours Opaque)
        if self.bg_path and os.path.exists(self.bg_path):
            try:
                # On remet l'alpha à 1 pour l'image de fond
                # (au cas où, même si c'est le début)
                self.image(self.bg_path, x=0, y=0, w=210, h=297)
            except: pass
        
        # 2. CONTENEUR : La "Feuille" avec TRANSPARENCE
        # On active la transparence à 85% (0.85)
        # Tu peux changer 0.85 vers 0.70 (plus transparent) ou 0.95 (plus opaque)
        self.set_alpha(0.85) 
        
        self.set_fill_color(255, 255, 255)
        self.rect(10, 10, 190, 277, 'F') 
        
        # IMPORTANT : On remet l'alpha à 1.0 (Opaque) pour le texte !
        # Sinon le texte sera aussi transparent et difficile à lire.
        self.set_alpha(1.0)

        # 3. EN-TÊTE DESIGN
        self.set_y(20) 
        
        # Titre Principal
        self.set_font('Helvetica', 'B', 24)
        self.set_text_color(184, 134, 11) # Or foncé
        self.cell(0, 10, "WASSAH EVENT", 0, 1, 'C')
        
        # Slogan
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(80, 80, 80) # Gris un peu plus sombre pour contrer la transparence
        self.cell(0, 8, "Des événements sur-mesure", 0, 1, 'C')
        
        # Ligne de séparation
        self.set_draw_color(184, 134, 11)
        self.set_line_width(0.5)
        x_line = (210 - 100) / 2
        self.line(x_line, self.get_y()+2, x_line + 100, self.get_y()+2)
        self.ln(10)

    def footer(self):
        self.set_y(-25)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Devis généré par Devo Pro - Document confidentiel", 0, 0, 'C')

# Fonction de génération
def generer_rendu_ia(info_client, df_panier, total_ttc, uploaded_bg_file):
    bg_path = None
    if uploaded_bg_file:
        file_ext = os.path.splitext(uploaded_bg_file.name)[1].lower()
        if not file_ext: file_ext = ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp_file:
            uploaded_bg_file.seek(0)
            temp_file.write(uploaded_bg_file.read())
            bg_path = temp_file.name
    
    pdf = FusionIA(bg_path=bg_path)
    pdf.add_page()
    
    # 1. Bloc TITRE DU DOCUMENT
    pdf.set_y(50)
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(40, 40, 40) 
    pdf.cell(0, 10, "DEVIS PRESTATION", 0, 1, 'R')
    pdf.ln(2)

    # 2. Bloc INFO CLIENT
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(0, 0, 0)
    
    txt_client = info_client if info_client else "Client Inconnu"
    for ligne in txt_client.split('\n'):
        safe_txt = str(ligne).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 6, txt=safe_txt, ln=True, align='R')
    
    pdf.ln(15) 
    
    # 3. TITRE DES PRESTATIONS
    pdf.set_font("Helvetica", 'B', 14)
    # Fond Marron avec Opacité 1.0 (car on a reset l'alpha dans header)
    pdf.set_text_color(255, 255, 255)
    pdf.set_fill_color(93, 64, 55)    
    
    pdf.cell(0, 10, " DÉTAIL DES PRESTATIONS ", 0, 1, 'C', fill=True)
    pdf.ln(5)
    
    # 4. LISTE DES PRODUITS
    pdf.set_font("Helvetica", size=12)
    pdf.set_text_color(20, 20, 20)
    
    # En-tête colonnes
    pdf.set_font("Helvetica", 'I', 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(100, 8, "Description", 0, 0, 'L')
    pdf.cell(30, 8, "Qté", 0, 0, 'C')
    pdf.cell(0, 8, "Montant", 0, 1, 'R')
    
    # Ligne séparation
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)

    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(0, 0, 0)

    for _, row in df_panier.iterrows():
        nom = row['Désignation']
        qte = int(row['Qté'])
        prix_u = row['Prix Unit.']
        total_ligne = prix_u * qte
        
        safe_nom = nom.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.cell(100, 8, f"- {safe_nom}", 0, 0, 'L')
        pdf.cell(30, 8, f"x {qte}", 0, 0, 'C')
        pdf.cell(0, 8, f"{total_ligne:.2f} E", 0, 1, 'R')
        
    # 5. TOTAL FINAL
    if pdf.get_y() > 240:
        pdf.add_page()
    
    pdf.set_y(230)
    
    pdf.set_draw_color(184, 134, 11)
    pdf.set_line_width(1)
    pdf.line(120, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(2)
    
    pdf.set_font("Helvetica", 'B', 16)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 12, f"TOTAL TTC : {total_ttc:.2f} EUR", 0, 1, 'R')
    
    try:
        if bg_path and os.path.exists(bg_path): os.unlink(bg_path)
    except: pass
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. INTERFACE UTILISATEUR ---
st.title("🥐 Devo : Wassah Event")

if 'panier_df' not in st.session_state: 
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])

c1, c2, c3 = st.columns([1, 1, 1.2])

with c1:
    st.subheader("👤 Infos Client")
    client_txt = st.text_area("Coordonnées...", height=180, placeholder="Nom du client\nDate\nAdresse complète")

with c2:
    st.subheader("📝 Commande")
    prod_txt = st.text_area("Produits (IA Detect)", value=st.session_state['produits_text'], height=180)
    st.session_state['produits_text'] = prod_txt
    if st.button("✨ Analyser", use_container_width=True):
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
        st.info(f"Total: **{tot:.2f} €**")
        
        pdf_bytes = generer_rendu_ia(client_txt, ed_df, tot, uploaded_bg)
        st.download_button("📩 Télécharger PDF", pdf_bytes, "devis_pro.pdf", "application/pdf", use_container_width=True)
