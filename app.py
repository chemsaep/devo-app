import streamlit as st
import pandas as pd
import re
from fpdf import FPDF
import streamlit_authenticator as stauth

# --- 1. CONFIGURATION ET SÉCURITÉ ---
st.set_page_config(page_title="Devo Pro", layout="wide", page_icon="🥐")

# Liste des utilisateurs
names = ['Administrateur']
usernames = ['admin']
passwords = ['1234'] 

# NOUVELLE SYNTAXE : Hachage sécurisé
Hasher = stauth.Hasher(passwords)
hashed_passwords = Hasher.generate()

# --- DÉFINITION DE LA VARIABLE CONFIG (Crucial pour éviter la NameError) ---
config = {
    'credentials': {
        'usernames': {
            usernames[0]: {
                'name': names[0],
                'password': hashed_passwords[0]
            }
        }
    },
    'cookie': {
        'expiry_days': 30,
        'key': 'signature_devo_key',
        'name': 'devo_cookie_auth'
    }
}

# Initialisation de l'authentification avec la variable config
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days']
)

# Formulaire de connexion
name, authentication_status, username = authenticator.login('Connexion', 'main')

if authentication_status:
    # --- 2. MENU DE PERSONNALISATION (SIDEBAR) ---
    st.sidebar.title(f"✨ Espace de {name}")
    authenticator.logout('Déconnexion', 'sidebar')
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Personnalisation du Devis")

    uploaded_bg = st.sidebar.file_uploader("Image de fond", type=["png", "jpg", "jpeg"])
    fond_final = uploaded_bg if uploaded_bg else "fond_devis.png"

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
    
    df_catalogue = st.sidebar.data_editor(df_catalogue, num_rows="dynamic", use_container_width=True)

    # --- 3. LOGIQUE PDF ---
    class PDF(FPDF):
        def header(self):
            try:
                self.image(fond_final, x=0, y=0, w=210, h=297)
            except:
                pass
            
            self.set_y(52) 
            self.set_font('Arial', 'I', 10)
            self.set_text_color(139, 115, 85)
            self.cell(0, 10, "Des événements sur-mesure pour toutes vos occasions", 0, 1, 'C')
            
            self.set_y(75)
            self.set_x(25) 
            self.set_font('Arial', '', 9)
            self.set_text_color(0, 0, 0)
            self.cell(0, 5, f"Contact : {contact_pro}", 0, 1, 'L')
            self.set_x(25)
            self.cell(0, 5, f"Insta : {insta_pro}", 0, 1, 'L')
            self.set_x(25)
            self.cell(0, 5, f"Lieu : {lieu_pro}", 0, 1, 'L')

        def footer(self):
            self.set_y(-55)
            self.set_font('Arial', '', 8)
            self.set_text_color(80, 80, 80)
            cond1 = "Conditions - Paiement possible en 2 fois (Acompte de 50% à payer lors de la réservation)"
            cond2 = "Aucun remboursement en cas d'annulation moins de 7 jours avant"
            self.cell(0, 4, cond1.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
            self.cell(0, 4, cond2.encode('latin-1', 'replace').decode('latin-1'), 0, 1, 'C')
            
            self.ln(5)
            self.set_font('Arial', 'I', 16)
            self.set_text_color(139, 115, 85)
            self.cell(0, 10, "MERCI DE VOTRE CONFIANCE", 0, 1, 'C')

    def generer_pdf(client_info, df_panier, total_ttc):
        pdf = PDF()
        pdf.add_page()
        
        pdf.set_y(75)
        pdf.set_right_margin(25)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 5, "Devis prestation déco :", 0, 1, 'R')
        pdf.set_font("Arial", size=10)
        for ligne in client_info:
            pdf.cell(0, 5, txt=str(ligne).encode('latin-1', 'replace').decode('latin-1'), ln=True, align='R')
        
        pdf.set_y(135) 
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

        pdf.set_y(220)
        pdf.set_font("Arial", 'B', 13)
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
        txt = st.text_area("Colle la demande client ici :", height=200)
        if st.button("✨ Analyser"):
            client, panier = analyser_texte(txt, df_catalogue)
            st.session_state['client_info'] = client
            st.session_state['panier_df'] = pd.DataFrame(panier)

    with col2:
        st.subheader("2. Le Devis Final")
        if not st.session_state['panier_df'].empty:
            edited_df = st.data_editor(st.session_state['panier_df'], use_container_width=True, num_rows="dynamic")
            total = (edited_df["Prix Unit."] * edited_df["Qté"]).sum()
            st.markdown(f"### Total : {total:.2f} €")
            pdf_bytes = generer_pdf(st.session_state['client_info'], edited_df, total)
            st.download_button("📩 Télécharger le PDF", pdf_bytes, f"devis_{username}.pdf", "application/pdf", use_container_width=True)

elif authentication_status == False:
    st.error('Identifiant ou mot de passe incorrect')
elif authentication_status == None:
    st.warning('Veuillez entrer vos identifiants.')
