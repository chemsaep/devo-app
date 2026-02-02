import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import streamlit_authenticator as stauth

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# Configuration des comptes (à personnaliser)
names = ['Administrateur']
usernames = ['admin']
passwords = ['1234']  # Change ce mot de passe pour plus de sécurité

hashed_passwords = stauth.Hasher(passwords).generate()

authenticator = stauth.Authenticate(
    {'usernames': {
        usernames[0]: {'name': names[0], 'password': hashed_passwords[0]}
    }},
    'devo_cookie',
    'signature_key',
    cookie_expiry_days=30
)

# Formulaire de connexion
name, authentication_status, username = authenticator.login('Connexion', 'main')

if authentication_status:
    # --- 2. MENU DE PERSONNALISATION (SIDEBAR) ---
    st.sidebar.title(f"✨ Espace de {name}")
    authenticator.logout('Déconnexion', 'sidebar')
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Personnalisation du Devis")

    # Choix du fond
    uploaded_bg = st.sidebar.file_uploader("Image de fond (PNG/JPG)", type=["png", "jpg", "jpeg"])
    fond_final = uploaded_bg if uploaded_bg else "fond_devis.png"

    # Infos Entreprise
    nom_pro = st.sidebar.text_input("Nom de l'entreprise", "Wassah Event")
    contact_pro = st.sidebar.text_input("Contact & Tel", "Ward - 06.65.62.00.92")
    insta_pro = st.sidebar.text_input("Instagram", "@wassah.event")
    lieu_pro = st.sidebar.text_input("Zone / Lieu", "94")

    # Gestion du Catalogue
    st.sidebar.subheader("💰 Tes Tarifs")
    try:
        df_catalogue = pd.read_csv("catalogue.csv")
    except:
        df_catalogue = pd.DataFrame(columns=["Produit", "Prix"])
    
    # Éditeur de catalogue en direct
    df_catalogue = st.sidebar.data_editor(df_catalogue, num_rows="dynamic", use_container_width=True)

    # --- 3. LOGIQUE PDF ---
    class PDF(FPDF):
        def header(self):
            try:
                self.image(fond_final, x=0, y=0, w=210, h=297)
            except:
                pass
            
            # En-tête sur-mesure
            self.set_y(52) 
            self.set_font('Arial', 'I', 11)
            self.set_text_color(139, 115, 85)
            self.cell(0, 10, f"Des événements sur-mesure - {nom_pro}", 0, 1, 'C')
            
            # Blocs infos alignés
            self.set_y(75)
            self.set_x(25) 
            self.set_font('Arial', '', 10)
            self.set_text_color(0, 0, 0)
            self.cell(0, 6, f"Contact : {contact_pro}", 0, 1, 'L')
            self.set_x(25)
            self.cell(0, 6, f"Insta : {insta_pro}", 0, 1, 'L')
            self.set_x(25)
            self.cell(0, 6, f"Lieu : {lieu_pro}", 0, 1, 'L')

    def generer_pdf(client_info, df_panier, total_ttc):
        pdf = PDF()
        pdf.add_page()
        
        # Bloc Client (Haut Droite)
        pdf.set_y(75)
        pdf.set_right_margin(25)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 6, "Devis prestation :", 0, 1, 'R')
        pdf.set_font("Arial", size=10)
        for ligne in client_info:
            pdf.cell(0, 6, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
        
        # Zone Prestations (Centre)
        pdf.set_y(130) 
        pdf.set_font("Arial", 'B', 14)
        pdf.set_text_color(93, 64, 55)
        pdf.cell(0, 10, "Prestations incluses", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_font("Arial", size=11)
        pdf.set_text_color(50, 50, 50)
        for _, row in df_panier.iterrows():
            nom = str(row['Désignation']).replace("[?] ", "").encode('latin-1', 'replace').decode('latin-1')
            pdf.set_x(40)
            pdf.cell(0, 8, f"- {nom} (x{int(row['Qté'])})", 0, 1, 'L')

        # Tarif Total
        pdf.set_y(215)
        pdf.set_font("Arial", 'B', 13)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, f"Tarif total : {total_ttc:.2f} EUR  ", 0, 1, 'R')
        
        return pdf.output(dest='S').encode('latin-1', 'replace')

    # --- 4. ANALYSE DU TEXTE ---
    def analyser_texte(texte, df_catalogue):
        lignes = texte.split('\n')
        infos_client = []
        panier_detecte = []
        for ligne in lignes:
            ligne = ligne.strip()
            if not ligne: continue
            match = re.search(r'(\d+)', ligne)
            if match and ("-" in ligne or any(p in ligne.lower() for p in ["box", "westaf", "brick"])):
                qte = int(match.group(1))
                nom_saisi = re.sub(r'[-\d+]', '', ligne).strip().lower()
                
                produit_trouve = None
                prix = 0.0
                for _, row in df_catalogue.iterrows():
                    if nom_saisi in str(row['Produit']).lower():
                        produit_trouve = row['Produit']
                        prix = float(row['Prix'])
                        break
                panier_detecte.append({"Désignation": produit_trouve if produit_trouve else f"[?] {nom_saisi}", "Prix Unit.": prix, "Qté": qte})
            else:
                infos_client.append(ligne)
        return infos_client, panier_detecte

    # --- 5. INTERFACE PRINCIPALE ---
    st.title(f"🥐 Devo : {nom_pro}")

    if 'panier_df' not in st.session_state:
        st.session_state['panier_df'] = pd.DataFrame(columns=["Désignation", "Prix Unit.", "Qté"])
    if 'client_info' not in st.session_state:
        st.session_state['client_info'] = []

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("1. La Demande")
        txt = st.text_area("Colle la demande client ici :", height=250, placeholder="Moussa Diop\n11/08/2026\n- 2 box gourmande")
        if st.button("✨ Analyser et Créer le Brouillon"):
            client, panier = analyser_texte(txt, df_catalogue)
            st.session_state['client_info'] = client
            st.session_state['panier_df'] = pd.DataFrame(panier)

    with col2:
        st.subheader("2. Le Devis Final")
        if not st.session_state['panier_df'].empty:
            edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
            
            # Calcul automatique du total
            total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
            st.markdown(f"### Total : {total:.2f} €")
            
            pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
            
            st.download_button(
                label="📩 Télécharger le PDF Personnalisé",
                data=pdf_bytes,
                file_name=f"devis_{nom_pro.lower().replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("En attente d'une analyse de message à gauche...")

elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer votre identifiant et votre mot de passe pour accéder à Devo.')
