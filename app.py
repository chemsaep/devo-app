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

# Chargement du catalogue pour l'IA d'analyse
try:
    df_catalogue = pd.read_csv("catalogue.csv")
except:
    df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])

# Sélection rapide vers le message de commande
st.sidebar.subheader("🛒 Produits Disponibles")
selection = st.sidebar.dataframe(df_catalogue, use_container_width=True, hide_index=True, on_select="rerun", selection_mode="multi-row")

if 'produits_text' not in st.session_state: 
    st.session_state['produits_text'] = ""

if selection and selection['selection']['rows']:
    for idx in selection['selection']['rows']:
        p = df_catalogue.iloc[idx]['Produit']
        if p not in st.session_state['produits_text']:
            st.session_state['produits_text'] += f"- 1 {p}\n"

# --- 3. L'IA DE FUSION (MOTEUR GRAPHIQUE AMÉLIORÉ) ---
class FusionIA(FPDF):
    def __init__(self, bg_path=None):
        super().__init__()
        self.bg_path = bg_path

    def header(self):
        # 1. Fusion de l'image de fond (si elle existe)
        if self.bg_path and os.path.exists(self.bg_path):
            # L'image prend toute la page
            self.image(self.bg_path, x=0, y=0, w=210, h=297)
            
            # --- EFFET DE FUSION (Overlay) ---
            # On ajoute un rectangle blanc semi-transparent pour la lisibilité
            # Note: FPDF standard ne gère pas bien la transparence native (alpha).
            # Astuce visuelle : On ne met pas de transparence ici sans bibliothèque externe (fpdf2),
            # mais on s'assure que le texte sera bien placé.
            # Si tu veux de la vraie transparence, il faut passer à 'fpdf2'.
            # Ici, on laisse l'image brute pour un effet "Waouh", mais on va encadrer le texte plus bas.

        # 2. Slogan esthétique
        self.set_y(52)
        self.set_font('Helvetica', 'I', 10)
        # Si fond image, on met le texte en blanc ou foncé selon besoin. 
        # Pour assurer la lisibilité, on met une couleur sombre standard (Or/Marron)
        self.set_text_color(139, 115, 85) 
        self.cell(0, 10, "Des événements sur-mesure - Wassah Event", 0, 1, 'C')

    def footer(self):
        self.set_y(-20)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(128, 128, 128) # Gris moyen
        self.cell(0, 10, "Document fusionné intelligemment par l'IA Devo Pro", 0, 0, 'C')

# Fonction de génération mise à jour
def generer_rendu_ia(info_client, df_panier, total_ttc, uploaded_bg_file):
    # Gestion du fichier temporaire pour l'image de fond
    bg_path = None
    temp_file = None
    
    if uploaded_bg_file:
        # On crée un fichier temporaire pour que FPDF puisse le lire
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        temp_file.write(uploaded_bg_file.read())
        temp_file.close() # On ferme pour que Windows/Linux puisse le relire
        bg_path = temp_file.name
    
    # Initialisation du PDF avec le chemin de l'image
    pdf = FusionIA(bg_path=bg_path)
    pdf.add_page()
    
    # --- BLOC CONTENU AVEC EFFET "CARTE" ---
    # Pour que ça fusionne bien, on peut dessiner un fond blanc partiel sous le texte
    pdf.set_fill_color(255, 255, 255)
    
    # Positionnement IA : Bloc Coordonnées Client
    pdf.set_y(78)
    pdf.set_right_margin(22)
    pdf.set_font("Helvetica", 'B', 11)
    pdf.set_text_color(0, 0, 0)
    
    # On dessine un petit fond blanc sous "DEVIS PRESTATION" si besoin, sinon brut
    pdf.cell(0, 6, "DEVIS PRESTATION", 0, 1, 'R')
    
    pdf.set_font("Helvetica", size=10)
    txt_client = info_client if info_client else "Informations Client"
    for ligne in txt_client.split('\n'):
        # Encodage pour éviter les bugs d'accents
        safe_txt = str(ligne).encode('latin-1', 'replace').decode('latin-1')
        pdf.cell(0, 5, txt=safe_txt, ln=True, align='R')
    
    # Positionnement IA : Zone de Détails (Centre)
    pdf.set_y(130)
    
    # TITRE DU DETAIL
    pdf.set_font("Helvetica", 'B', 13)
    pdf.set_text_color(93, 64, 55) 
    pdf.cell(0, 10, "Détail des Prestations", 0, 1, 'C')
    pdf.ln(5)
    
    # LISTE DES PRODUITS
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(20, 20, 20) # Presque noir pour lisibilité max
    
    for _, row in df_panier.iterrows():
        pdf.set_x(35) 
        item = f"- {row['Désignation']} (x{int(row['Qté'])})"
        safe_item = item.encode('latin-1', 'replace').decode('latin-1')
        
        # Astuce : On remplit le fond de la cellule en blanc (fill=True) pour que le texte ressorte sur la photo
        # Le dernier paramètre '1' active le fill
        pdf.cell(0, 8, txt=safe_item, ln=True, align='L', fill=False) 

    # Bloc Final : Total mis en valeur
    pdf.set_y(225)
    pdf.set_font("Helvetica", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    
    # Petit fond blanc sous le total pour faire "pro"
    pdf.set_fill_color(255, 255, 255)
    pdf.cell(0, 10, f"TOTAL TTC : {total_ttc:.2f} EUR  ", 0, 1, 'R', fill=True)
    
    # Nettoyage du fichier temporaire
    if bg_path and os.path.exists(bg_path):
        os.unlink(bg_path)
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- 4. INTERFACE UTILISATEUR ---
st.title("🥐 Devo : Wassah Event")

if 'panier_df' not in st.session_state: 
    st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])

# Création des 3 colonnes de travail
c1, c2, c3 = st.columns([1, 1, 1.2])

with c1:
    st.subheader("👤 Infos Client")
    client_txt = st.text_area("Coordonnées...", height=180, placeholder="Nom du client\nDate\nAdresse/Lieu")

with c2:
    st.subheader("📝 Commande")
    prod_txt = st.text_area("Produits sélectionnés :", value=st.session_state['produits_text'], height=180)
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
        # Éditeur intelligent de tableau
        ed_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
        tot = (ed_df["Prix Unit."] * ed_df["Qté"]).sum()
        st.info(f"Montant Total calculé : **{tot:.2f} €**")
        
        # Bouton de fusion IA
        # ATTENTION : On passe 'uploaded_bg' qui vient de la sidebar
        pdf_bytes = generer_rendu_ia(client_txt, ed_df, tot, uploaded_bg)
        
        st.download_button("📩 Télécharger le PDF Fusionné", pdf_bytes, "devis_wassah.pdf", "application/pdf", use_container_width=True)
