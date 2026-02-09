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

# --- 3. L'IA DE FUSION (MOTEUR GRAPHIQUE GRIS TRANSPARENT) ---
class FusionIA(FPDF):
    def __init__(self, bg_path=None):
        super().__init__()
        self.bg_path = bg_path
        self.ext_gstates = [] 
        # Force la version PDF 1.4 pour supporter la transparence
        self.pdf_version = '1.4' 

    # --- FONCTIONS TECHNIQUES TRANSPARENCE ---
    def set_alpha(self, alpha, bm='Normal'):
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
    # ----------------------------------------------------------

    def header(self):
        # 1. FOND IMAGE
        if self.bg_path and os.path.exists(self.bg_path):
            try:
                self.image(self.bg_path, x=0, y=0, w=210, h=297)
            except: pass
        
        # 2. CALQUE GRIS TRANSPARENT
        # REGLAGE DU "VOILE"
        self.set_alpha(0.60) # 0.60 = On voit bien l'image à travers
        
        # COULEUR GRISE LEGERE (RGB: 240, 240, 240)
        self.set_fill_color(240, 240, 240) 
        
        # Marge de 15mm sur les côtés
        self.rect(15, 15, 180, 267, 'F') 
        
        # IMPORTANT : On remet l'opacité à 100% pour le texte
        self.set_alpha(1.0) 

        # 3. TITRE "DEVIS"
        self.set_y(25) 
        self.set_font('Times', '', 45) 
        self.set_text_color(80, 80, 80) # Gris foncé élégant
        self.cell(0, 15, "D E V I S", 0, 1, 'C')
        
        # Sous-titre
        self.set_font('Times', 'I', 14)
        self.set_text_color(50, 50, 50) 
        self.cell(0, 10, "Wassah Event - Des événements sur-mesure", 0, 1, 'C')
        
        # Ligne de séparation
        self.set_draw_color(100, 100, 100)
        self.set_line_width(0.3)
        self.line(40, self.get_y()+2, 170, self.get_y()+2)
        self.ln(10)

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "Document généré par Devo Pro", 0, 0, 'C')

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
    
    # --- MISE EN PAGE CONTENU ---
    y_start = 65 
    pdf.set_y(y_start)
    
    # --- BLOC DOUBLE COLONNE ---
    pdf.set_font("Helvetica", size=10)
    pdf.set_text_color(10, 10, 10) # Texte presque noir
    
    # COLONNE GAUCHE (Tes infos)
    x_left = 25
    pdf.set_xy(x_left, y_start)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(80, 5, "Contact :", 0, 1)
    pdf.set_font("Helvetica", size=10)
    pdf.set_x(x_left)
    pdf.cell(80, 5, "Tel : 06.65.62.00.92", 0, 1)
    pdf.set_x(x_left)
    pdf.cell(80, 5, "Insta : @wassah.event", 0, 1)
    pdf.set_x(x_left)
    pdf.cell(80, 5, "Lieu : Île-de-France", 0, 1)

    # COLONNE DROITE (Infos Client)
    x_right = 110
    pdf.set_xy(x_right, y_start)
    pdf.set_font("Helvetica", 'B', 10)
    pdf.cell(80, 5, "Devis pour :", 0, 1, 'R')
    
    pdf.set_font("Helvetica", size=10)
    txt_client = info_client if info_client else "Client Inconnu"
    for ligne in txt_client.split('\n'):
        safe_txt = str(ligne).encode('latin-1', 'replace').decode('latin-1')
        pdf.set_x(x_right)
        pdf.cell(80, 5, txt=safe_txt, ln=True, align='R')
    
    # --- TITRE THEME ---
    pdf.set_y(pdf.get_y() + 15)
    pdf.set_font("Times", 'I', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, "Détail de la prestation", 0, 1, 'C')
    
    # --- LISTE DES PRESTATIONS ---
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(0, 0, 0)
    
    for _, row in df_panier.iterrows():
        nom = row['Désignation']
        qte = int(row['Qté'])
        
        safe_nom = nom.encode('latin-1', 'replace').decode('latin-1')
        item_text = f"{safe_nom}"
        if qte > 1:
            item_text += f" (x{qte})"
            
        pdf.cell(0, 7, item_text, 0, 1, 'C')
        
    # --- PRIX TOTAL ---
    pdf.ln(15)
    
    x_sep = (210 - 50) / 2
    pdf.set_draw_color(100, 100, 100)
    pdf.line(x_sep, pdf.get_y(), x_sep + 50, pdf.get_y())
    pdf.ln(5)
    
    pdf.set_font("Helvetica", 'B', 12)
    pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR", 0, 1, 'C')
    
    # Conditions
    pdf.ln(5)
    pdf.set_font("Helvetica", size=8)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 4, "Conditions : Paiement possible en 2 fois (Acompte 50%).\nAucun remboursement en cas d'annulation moins de 7 jours avant.", 0, 'C')
    
    # --- MERCI (Bas de page) ---
    pdf.set_y(240)
    pdf.set_font("Times", 'I', 22)
    pdf.set_text_color(160, 120, 90) # Garde une touche dorée pour le merci
    pdf.cell(0, 10, "MERCI DE VOTRE CONFIANCE", 0, 1, 'C')

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
    client_txt = st.text_area("Coordonnées...", height=180, placeholder="Nom : Khadija\nDate : 08/11/2025\nLieu : Sarcelles")

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
